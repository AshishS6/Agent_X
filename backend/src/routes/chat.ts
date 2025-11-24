import { Router, Request, Response } from 'express';
import axios from 'axios';
import { config } from '../config';

const router = Router();

/**
 * POST /api/chat - Send a message to the local LLM
 */
router.post('/', async (req: Request, res: Response) => {
    try {
        const { message, history } = req.body;

        if (!message) {
            return res.status(400).json({
                success: false,
                error: 'Message is required'
            });
        }

        // Construct the prompt context from history if available
        // For simple chat, we'll just send the messages array if the provider supports it,
        // or concatenate for simpler models.
        // DeepSeek-R1 via Ollama supports the /api/chat endpoint with a messages array.

        const messages = history ? [...history, { role: 'user', content: message }] : [{ role: 'user', content: message }];

        // Call Ollama
        // We use the configured OLLAMA_BASE_URL and LLM_MODEL
        const ollamaUrl = `${config.llm.ollama.baseUrl}/api/chat`;

        // Note: We are NOT streaming for the MVP to keep it simple and robust.
        const response = await axios.post(ollamaUrl, {
            model: config.llm.ollama.model,
            messages: messages,
            stream: false
        });

        if (response.data && response.data.message) {
            res.json({
                success: true,
                data: {
                    role: response.data.message.role,
                    content: response.data.message.content
                }
            });
        } else {
            throw new Error('Invalid response from LLM provider');
        }

    } catch (error: any) {
        console.error('Error in chat endpoint:', error.message);
        // Fallback error handling
        res.status(500).json({
            success: false,
            error: error.response?.data?.error || error.message || 'Failed to communicate with AI'
        });
    }
});

export default router;
