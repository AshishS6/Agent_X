import express, { Express, Request, Response, NextFunction } from 'express';
import cors from 'cors';
import { config } from './config';
import { db } from './services/db.service';
import { queueService } from './services/queue.service';

// Import routes
import agentsRouter from './routes/agents';
import tasksRouter from './routes/tasks';
import monitoringRouter from './routes/monitoring';
import integrationsRouter from './routes/integrations';
import chatRouter from './routes/chat';

const app: Express = express();

// Middleware
app.use(cors({ origin: config.cors.origin }));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging middleware
app.use((req: Request, res: Response, next: NextFunction) => {
    console.log(`${req.method} ${req.path}`, {
        query: req.query,
        body: req.method !== 'GET' ? req.body : undefined
    });
    next();
});

// API Routes
app.use('/api/agents', agentsRouter);
app.use('/api/tasks', tasksRouter);
app.use('/api/monitoring', monitoringRouter);
app.use('/api/integrations', integrationsRouter);
app.use('/api/chat', chatRouter);

// Root endpoint
app.get('/', (req: Request, res: Response) => {
    res.json({
        name: 'Agent_X Backend API',
        version: '1.0.0',
        status: 'running',
        endpoints: {
            agents: '/api/agents',
            tasks: '/api/tasks',
            monitoring: '/api/monitoring',
            health: '/api/monitoring/health',
        },
    });
});

// 404 handler
app.use((req: Request, res: Response) => {
    res.status(404).json({
        success: false,
        error: 'Endpoint not found'
    });
});

// Error handler
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
    console.error('Unhandled error:', err);
    res.status(500).json({
        success: false,
        error: err.message || 'Internal server error'
    });
});

// Graceful shutdown
const gracefulShutdown = async () => {
    console.log('Shutting down gracefully...');
    try {
        await db.close();
        await queueService.close();
        process.exit(0);
    } catch (error) {
        console.error('Error during shutdown:', error);
        process.exit(1);
    }
};

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);

// Start server
const startServer = async () => {
    try {
        // Test database connection
        const dbHealthy = await db.ping();
        if (!dbHealthy) {
            throw new Error('Database connection failed');
        }
        console.log('✅ Database connected');

        // Test Redis connection
        const redisHealthy = await queueService.ping();
        if (!redisHealthy) {
            throw new Error('Redis connection failed');
        }
        console.log('✅ Redis connected');

        // Start Express server
        app.listen(config.port, () => {
            console.log(`🚀 Server running on port ${config.port}`);
            console.log(`📡 Environment: ${config.nodeEnv}`);
            console.log(`🌐 CORS enabled for: ${config.cors.origin}`);
            console.log(`\n📍 API Documentation:`);
            console.log(`   - Health: http://localhost:${config.port}/api/monitoring/health`);
            console.log(`   - Agents: http://localhost:${config.port}/api/agents`);
            console.log(`   - Tasks: http://localhost:${config.port}/api/tasks`);
            console.log(`   - Metrics: http://localhost:${config.port}/api/monitoring/metrics\n`);
        });
    } catch (error) {
        console.error('❌ Failed to start server:', error);
        process.exit(1);
    }
};

startServer();

export default app;
