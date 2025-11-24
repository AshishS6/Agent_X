import { Router, Request, Response } from 'express';
import { AgentModel } from '../models/Agent';
import { TaskModel } from '../models/Task';
import { queueService } from '../services/queue.service';
import { ApiResponse, QueueMessage } from '../types';
import { v4 as uuidv4 } from 'uuid';

const router = Router();

/**
 * GET /api/agents - Get all agents
 */
router.get('/', async (req: Request, res: Response<ApiResponse>) => {
    try {
        const agents = await AgentModel.findAll();
        res.json({ success: true, data: agents });
    } catch (error: any) {
        console.error('Error fetching agents:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

/**
 * GET /api/agents/:id - Get agent by ID
 */
router.get('/:id', async (req: Request, res: Response<ApiResponse>) => {
    try {
        const agent = await AgentModel.findById(req.params.id);
        if (!agent) {
            return res.status(404).json({ success: false, error: 'Agent not found' });
        }
        res.json({ success: true, data: agent });
    } catch (error: any) {
        console.error('Error fetching agent:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

/**
 * POST /api/agents/:id/execute - Execute agent with task
 */
router.post('/:id/execute', async (req: Request, res: Response<ApiResponse>) => {
    try {
        const agent = await AgentModel.findById(req.params.id);
        if (!agent) {
            return res.status(404).json({ success: false, error: 'Agent not found' });
        }

        if (agent.status !== 'active') {
            return res.status(400).json({
                success: false,
                error: `Agent is ${agent.status}, cannot execute`
            });
        }

        const { action, input, priority = 'medium' } = req.body;

        if (!action || !input) {
            return res.status(400).json({
                success: false,
                error: 'Missing required fields: action, input'
            });
        }

        // Create task in database
        const task = await TaskModel.create({
            agentId: agent.id,
            userId: req.body.userId,
            action,
            input,
            status: 'pending',
            priority,
        });

        // Enqueue task
        const queueMessage: QueueMessage = {
            taskId: task.id,
            agentType: agent.type,
            action,
            input,
            userId: req.body.userId,
            timestamp: new Date().toISOString(),
            priority,
        };

        await queueService.enqueueTask(queueMessage);
        await queueService.publishEvent('task_created', { taskId: task.id, agentType: agent.type });

        res.json({
            success: true,
            data: task,
            message: 'Task enqueued successfully'
        });
    } catch (error: any) {
        console.error('Error executing agent:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

/**
 * PUT /api/agents/:id - Update agent
 */
router.put('/:id', async (req: Request, res: Response<ApiResponse>) => {
    try {
        const agent = await AgentModel.update(req.params.id, req.body);
        if (!agent) {
            return res.status(404).json({ success: false, error: 'Agent not found' });
        }
        res.json({ success: true, data: agent });
    } catch (error: any) {
        console.error('Error updating agent:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

/**
 * GET /api/agents/:id/metrics - Get agent metrics
 */
router.get('/:id/metrics', async (req: Request, res: Response<ApiResponse>) => {
    try {
        const agent = await AgentModel.findById(req.params.id);
        if (!agent) {
            return res.status(404).json({ success: false, error: 'Agent not found' });
        }

        const statusCounts = await TaskModel.getStatusCounts(agent.id);
        const recentTasks = await TaskModel.findAll({ agentId: agent.id, limit: 10 });

        res.json({
            success: true,
            data: {
                statusCounts,
                recentTasks,
                totalTasks: Object.values(statusCounts).reduce((a, b) => a + b, 0),
            }
        });
    } catch (error: any) {
        console.error('Error fetching agent metrics:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

export default router;
