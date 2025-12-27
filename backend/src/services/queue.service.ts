import Redis from 'ioredis';
import { config } from '../config';
import { QueueMessage } from '../types';

class QueueService {
    private redis: Redis;
    private readonly PENDING_QUEUE = 'tasks:pending';
    private readonly COMPLETED_QUEUE = 'tasks:completed';
    private readonly FAILED_QUEUE = 'tasks:failed';
    private readonly EVENTS_STREAM = 'events:system';

    constructor() {
        this.redis = new Redis(config.redis.url);

        this.redis.on('error', (err) => {
            console.error('Redis connection error:', err);
        });

        this.redis.on('connect', () => {
            console.log('Redis connected successfully');
        });
    }

    /**
     * Enqueue a task to the pending queue
     */
    async enqueueTask(message: QueueMessage): Promise<string> {
        const messageId = await this.redis.xadd(
            this.PENDING_QUEUE,
            '*',
            'data',
            JSON.stringify(message)
        );

        console.log(`Enqueued task ${message.taskId} to pending queue`, { messageId });

        // Also add to agent-specific queue for targeted consumption
        const agentQueue = `tasks:${message.agentType}`;
        await this.redis.xadd(agentQueue, '*', 'data', JSON.stringify(message));

        return messageId || '';
    }

    /**
     * Mark task as completed
     */
    async completeTask(taskId: string, result: any): Promise<void> {
        await this.redis.xadd(
            this.COMPLETED_QUEUE,
            '*',
            'taskId',
            taskId,
            'result',
            JSON.stringify(result),
            'timestamp',
            new Date().toISOString()
        );
    }

    /**
     * Mark task as failed
     */
    async failTask(taskId: string, error: string): Promise<void> {
        await this.redis.xadd(
            this.FAILED_QUEUE,
            '*',
            'taskId',
            taskId,
            'error',
            error,
            'timestamp',
            new Date().toISOString()
        );
    }

    /**
     * Publish system event
     */
    async publishEvent(type: string, payload: any): Promise<void> {
        await this.redis.xadd(
            this.EVENTS_STREAM,
            '*',
            'type',
            type,
            'payload',
            JSON.stringify(payload),
            'timestamp',
            new Date().toISOString()
        );
    }

    /**
     * Read messages from a queue/stream
     */
    async readMessages(
        stream: string,
        lastId: string = '0-0',
        count: number = 10
    ): Promise<any[]> {
        const results = await this.redis.xread(
            'COUNT',
            count,
            'STREAMS',
            stream,
            lastId
        );

        if (!results) return [];

        const [, messages] = results[0];
        return messages.map(([id, fields]: any) => ({
            id,
            data: this.parseFields(fields),
        }));
    }

    /**
     * Get queue length
     */
    async getQueueLength(stream: string): Promise<number> {
        return await this.redis.xlen(stream);
    }

    /**
     * Health check
     */
    async ping(): Promise<boolean> {
        try {
            const result = await this.redis.ping();
            return result === 'PONG';
        } catch (error) {
            return false;
        }
    }

    /**
     * Close connection
     */
    async close(): Promise<void> {
        await this.redis.quit();
    }

    private parseFields(fields: string[]): Record<string, any> {
        const result: Record<string, any> = {};
        for (let i = 0; i < fields.length; i += 2) {
            const key = fields[i];
            const value = fields[i + 1];

            // Try to parse JSON values
            try {
                result[key] = JSON.parse(value);
            } catch {
                result[key] = value;
            }
        }
        return result;
    }
}

export const queueService = new QueueService();
