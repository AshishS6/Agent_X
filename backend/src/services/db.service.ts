import { Pool } from 'pg';
import { config } from '../config';

class DatabaseService {
    private pool: Pool;

    constructor() {
        this.pool = new Pool({
            connectionString: config.database.url,
        });

        this.pool.on('error', (err) => {
            console.error('Unexpected database error:', err);
        });
    }

    async query(text: string, params?: any[]) {
        const start = Date.now();
        try {
            const result = await this.pool.query(text, params);
            const duration = Date.now() - start;
            console.log('Executed query', { text, duration, rows: result.rowCount });
            return result;
        } catch (error) {
            console.error('Database query error:', error);
            throw error;
        }
    }

    async getClient() {
        return await this.pool.connect();
    }

    async close() {
        await this.pool.end();
    }

    // Health check
    async ping(): Promise<boolean> {
        try {
            await this.query('SELECT 1');
            return true;
        } catch (error) {
            return false;
        }
    }
}

export const db = new DatabaseService();
