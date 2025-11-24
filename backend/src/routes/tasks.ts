import { Router, Request, Response } from 'express';
import { TaskModel } from '../models/Task';
import { ApiResponse } from '../types';

const router = Router();

/**
 * GET /api/tasks - Get all tasks with filters
 */
router.get('/', async (req: Request, res: Response<ApiResponse>) => {
    try {
        const filters = {
            agentId: req.query.agentId as string,
            status: req.query.status as any,
            userId: req.query.userId as string,
            limit: req.query.limit ? parseInt(req.query.limit as string, 10) : 50,
            offset: req.query.offset ? parseInt(req.query.offset as string, 10) : 0,
        };

        const tasks = await TaskModel.findAll(filters);
        res.json({ success: true, data: tasks });
    } catch (error: any) {
        console.error('Error fetching tasks:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

/**
 * GET /api/tasks/:id - Get task by ID
 */
router.get('/:id', async (req: Request, res: Response<ApiResponse>) => {
    try {
        const task = await TaskModel.findById(req.params.id);
        if (!task) {
            return res.status(404).json({ success: false, error: 'Task not found' });
        }
        res.json({ success: true, data: task });
    } catch (error: any) {
        console.error('Error fetching task:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

/**
 * GET /api/tasks/status/counts - Get task counts by status
 */
router.get('/status/counts', async (req: Request, res: Response<ApiResponse>) => {
    try {
        const agentId = req.query.agentId as string | undefined;
        const counts = await TaskModel.getStatusCounts(agentId);
        res.json({ success: true, data: counts });
    } catch (error: any) {
        console.error('Error fetching task counts:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

export default router;
