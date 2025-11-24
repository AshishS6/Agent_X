import { Router, Request, Response } from 'express';
import { db } from '../services/db.service';
import { queueService } from '../services/queue.service';
import { AgentModel } from '../models/Agent';
import { TaskModel } from '../models/Task';
import { ApiResponse } from '../types';

const router = Router();

/**
 * GET /api/monitoring/health - System health check
 */
router.get('/health', async (req: Request, res: Response<ApiResponse>) => {
    try {
        const health = {
            status: 'healthy',
            timestamp: new Date().toISOString(),
            services: {
                database: await db.ping(),
                redis: await queueService.ping(),
            },
        };

        const allHealthy = Object.values(health.services).every((s) => s === true);

        res.status(allHealthy ? 200 : 503).json({
            success: allHealthy,
            data: health
        });
    } catch (error: any) {
        console.error('Health check error:', error);
        res.status(503).json({
            success: false,
            error: 'Health check failed',
            data: { status: 'unhealthy' }
        });
    }
});

/**
 * GET /api/monitoring/metrics - Real-time system metrics
 */
router.get('/metrics', async (req: Request, res: Response<ApiResponse>) => {
    try {
        const agents = await AgentModel.findAll();
        const taskCounts = await TaskModel.getStatusCounts();
        const recentTasks = await TaskModel.findAll({ limit: 10 });

        // Calculate active agents
        const activeAgents = agents.filter((a) => a.status === 'active').length;

        // Calculate time saved (mock calculation - would be based on actual data)
        const completedTasks = taskCounts.completed || 0;
        const avgTimeSavedPerTask = 0.5; // hours
        const timeSaved = (completedTasks * avgTimeSavedPerTask).toFixed(1);

        // Calculate efficiency score
        const totalCompleted = taskCounts.completed || 0;
        const totalFailed = taskCounts.failed || 0;
        const total = totalCompleted + totalFailed;
        const efficiencyScore = total > 0
            ? ((totalCompleted / total) * 100).toFixed(1)
            : 100;

        const metrics = {
            activeAgents: {
                value: `${activeAgents}/${agents.length}`,
                count: activeAgents,
                total: agents.length,
            },
            tasksCompleted: {
                value: taskCounts.completed || 0,
                trend: 8.5, // Would calculate from historical data
            },
            timeSaved: {
                value: `${timeSaved}h`,
                hours: parseFloat(timeSaved),
            },
            efficiencyScore: {
                value: `${efficiencyScore}%`,
                score: parseFloat(efficiencyScore),
            },
            taskBreakdown: taskCounts,
            recentActivity: recentTasks,
        };

        res.json({ success: true, data: metrics });
    } catch (error: any) {
        console.error('Error fetching metrics:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

/**
 * GET /api/monitoring/activity - Recent system activity
 */
router.get('/activity', async (req: Request, res: Response<ApiResponse>) => {
    try {
        const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : 20;
        const tasks = await TaskModel.findAll({ limit });

        // Format tasks as activity feed
        const activity = tasks.map((task) => ({
            id: task.id,
            taskId: task.id,
            agentId: task.agentId,
            action: task.action,
            status: task.status,
            timestamp: task.createdAt,
            metadata: {
                input: task.input,
                output: task.output,
            },
        }));

        res.json({ success: true, data: activity });
    } catch (error: any) {
        console.error('Error fetching activity:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

export default router;
