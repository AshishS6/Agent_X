import dotenv from 'dotenv';

dotenv.config();

export const config = {
    port: parseInt(process.env.PORT || '3001', 10),
    nodeEnv: process.env.NODE_ENV || 'development',

    database: {
        url: process.env.DATABASE_URL || 'postgresql://postgres:dev_password@localhost:5432/agentx',
    },

    redis: {
        url: process.env.REDIS_URL || 'redis://localhost:6379',
    },

    llm: {
        openai: {
            apiKey: process.env.OPENAI_API_KEY,
            model: process.env.OPENAI_MODEL || 'gpt-4-turbo-preview',
        },
        anthropic: {
            apiKey: process.env.ANTHROPIC_API_KEY,
            model: process.env.ANTHROPIC_MODEL || 'claude-3-sonnet-20240229',
        },
        ollama: {
            baseUrl: process.env.OLLAMA_BASE_URL || 'http://localhost:11434',
            model: process.env.OLLAMA_MODEL || 'llama3',
        },
    },

    cors: {
        origin: (process.env.FRONTEND_URL || 'http://localhost:5173').split(','),
    },

    logging: {
        level: process.env.LOG_LEVEL || 'info',
    },
};
