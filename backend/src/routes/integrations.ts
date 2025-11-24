import { Router, Request, Response } from 'express';
import { IntegrationModel } from '../models/Integration';
import { ApiResponse } from '../types';

const router = Router();

/**
 * GET /api/integrations - Get all integrations
 */
router.get('/', async (req: Request, res: Response<ApiResponse>) => {
    try {
        const integrations = await IntegrationModel.findAll();
        res.json({ success: true, data: integrations });
    } catch (error: any) {
        console.error('Error fetching integrations:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

/**
 * GET /api/integrations/:id - Get integration by ID
 */
router.get('/:id', async (req: Request, res: Response<ApiResponse>) => {
    try {
        const integration = await IntegrationModel.findById(req.params.id);
        if (!integration) {
            return res.status(404).json({ success: false, error: 'Integration not found' });
        }
        res.json({ success: true, data: integration });
    } catch (error: any) {
        console.error('Error fetching integration:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

/**
 * POST /api/integrations - Create new integration
 */
router.post('/', async (req: Request, res: Response<ApiResponse>) => {
    try {
        const integration = await IntegrationModel.create(req.body);
        res.status(201).json({ success: true, data: integration });
    } catch (error: any) {
        console.error('Error creating integration:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

/**
 * PUT /api/integrations/:id - Update integration
 */
router.put('/:id', async (req: Request, res: Response<ApiResponse>) => {
    try {
        const integration = await IntegrationModel.update(req.params.id, req.body);
        if (!integration) {
            return res.status(404).json({ success: false, error: 'Integration not found' });
        }
        res.json({ success: true, data: integration });
    } catch (error: any) {
        console.error('Error updating integration:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

/**
 * DELETE /api/integrations/:id - Delete integration
 */
router.delete('/:id', async (req: Request, res: Response<ApiResponse>) => {
    try {
        const success = await IntegrationModel.delete(req.params.id);
        if (!success) {
            return res.status(404).json({ success: false, error: 'Integration not found' });
        }
        res.json({ success: true, message: 'Integration deleted successfully' });
    } catch (error: any) {
        console.error('Error deleting integration:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

export default router;
