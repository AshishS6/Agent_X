import { Router, Request, Response } from 'express';
import { db } from '../services/db.service';
import { queueService } from '../services/queue.service';
import { AgentModel } from '../models/Agent';
import { TaskModel } from '../models/Task';
import { ApiResponse } from '../types';
import axios from 'axios';

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
            : "100";

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
        const activity = tasks.tasks.map((task: any) => ({
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

/**
 * GET /api/monitoring/proxy - Proxy for site previews to bypass iframe blocking
 */
router.get('/proxy', async (req: Request, res: Response) => {
    try {
        const targetUrl = req.query.url as string;
        if (!targetUrl) {
            return res.status(400).send('URL is required');
        }

        console.log(`Proxying request for: ${targetUrl}`);

        const response = await axios.get(targetUrl, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            timeout: 10000,
            validateStatus: () => true
        });

        let html = response.data;

        // If it's not a string (e.g. binary), just send it as is or handle appropriately
        if (typeof html !== 'string') {
            return res.status(response.status).send(html);
        }

        // Inject <base> tag to fix relative links (CSS, JS, Images)
        const baseUrl = new URL(targetUrl).origin;
        const baseTag = `<base href="${baseUrl}/">`;

        if (html.includes('<head>')) {
            html = html.replace('<head>', `<head>\n    ${baseTag}`);
        } else if (html.includes('<html>')) {
            html = html.replace('<html>', `<html>\n<head>\n    ${baseTag}\n</head>`);
        } else {
            html = baseTag + html;
        }

        // Remove security headers that prevent iframe embedding
        res.removeHeader('X-Frame-Options');
        res.removeHeader('Content-Security-Policy');

        // Set content type and send
        res.set('Content-Type', 'text/html');
        res.send(html);
    } catch (error: any) {
        console.error('Proxy error:', error);
        res.status(500).send(`Failed to proxy site: ${error.message}`);
    }
});

export default router;
