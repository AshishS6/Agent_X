import { db } from '../services/db.service';
import { Task, TaskStatus, TaskPriority } from '../types';
import { v4 as uuidv4 } from 'uuid';

export class TaskModel {
    /**
     * Get all tasks with optional filters
     */
    static async findAll(filters?: {
        agentId?: string;
        status?: TaskStatus;
        userId?: string;
        limit?: number;
        offset?: number;
    }): Promise<{ tasks: Task[], total: number }> {
        let query = 'SELECT * FROM tasks WHERE 1=1';
        let countQuery = 'SELECT COUNT(*)::int as total FROM tasks WHERE 1=1';
        const params: any[] = [];
        let paramCount = 1;

        if (filters?.agentId) {
            const clause = ` AND agent_id = $${paramCount++}`;
            query += clause;
            countQuery += clause;
            params.push(filters.agentId);
        }
        if (filters?.status) {
            const clause = ` AND status = $${paramCount++}`;
            query += clause;
            countQuery += clause;
            params.push(filters.status);
        }
        if (filters?.userId) {
            const clause = ` AND user_id = $${paramCount++}`;
            query += clause;
            countQuery += clause;
            params.push(filters.userId);
        }

        query += ' ORDER BY created_at DESC';

        if (filters?.limit) {
            query += ` LIMIT $${paramCount++}`;
            params.push(filters.limit);
        }
        if (filters?.offset) {
            query += ` OFFSET $${paramCount++}`;
            params.push(filters.offset);
        }

        // Execute both queries
        // Note: For count query, we only need the filter params, not limit/offset
        const filterParams = params.slice(0, paramCount - 1 - (filters?.limit ? 1 : 0) - (filters?.offset ? 1 : 0));

        const [result, countResult] = await Promise.all([
            db.query(query, params),
            db.query(countQuery, filterParams)
        ]);

        return {
            tasks: result.rows,
            total: countResult.rows[0].total
        };
    }

    /**
     * Get task by ID
     */
    static async findById(id: string): Promise<Task | null> {
        const result = await db.query('SELECT * FROM tasks WHERE id = $1', [id]);
        return result.rows[0] || null;
    }

    /**
     * Create new task
     */
    static async create(data: Omit<Task, 'id' | 'createdAt'>): Promise<Task> {
        const id = uuidv4();
        const result = await db.query(
            `INSERT INTO tasks (id, agent_id, user_id, action, input, status, priority)
       VALUES ($1, $2, $3, $4, $5, $6, $7)
       RETURNING *`,
            [
                id,
                data.agentId,
                data.userId || null,
                data.action,
                JSON.stringify(data.input),
                data.status,
                data.priority,
            ]
        );
        return result.rows[0];
    }

    /**
     * Update task
     */
    static async update(id: string, data: Partial<Task>): Promise<Task | null> {
        const updates: string[] = [];
        const values: any[] = [];
        let paramCount = 1;

        if (data.status !== undefined) {
            updates.push(`status = $${paramCount++}`);
            values.push(data.status);
        }
        if (data.output !== undefined) {
            updates.push(`output = $${paramCount++}`);
            values.push(JSON.stringify(data.output));
        }
        if (data.error !== undefined) {
            updates.push(`error = $${paramCount++}`);
            values.push(data.error);
        }
        if (data.startedAt !== undefined) {
            updates.push(`started_at = $${paramCount++}`);
            values.push(data.startedAt);
        }
        if (data.completedAt !== undefined) {
            updates.push(`completed_at = $${paramCount++}`);
            values.push(data.completedAt);
        }

        if (updates.length === 0) {
            return await this.findById(id);
        }

        values.push(id);

        const result = await db.query(
            `UPDATE tasks SET ${updates.join(', ')} WHERE id = $${paramCount} RETURNING *`,
            values
        );

        return result.rows[0] || null;
    }

    /**
     * Get task counts by status
     */
    static async getStatusCounts(agentId?: string): Promise<Record<TaskStatus, number>> {
        let query = 'SELECT status, COUNT(*)::int as count FROM tasks';
        const params: any[] = [];

        if (agentId) {
            query += ' WHERE agent_id = $1';
            params.push(agentId);
        }

        query += ' GROUP BY status';

        const result = await db.query(query, params);

        const counts: Record<string, number> = {
            pending: 0,
            processing: 0,
            completed: 0,
            failed: 0,
        };

        result.rows.forEach((row) => {
            counts[row.status] = row.count;
        });

        return counts as Record<TaskStatus, number>;
    }
}
