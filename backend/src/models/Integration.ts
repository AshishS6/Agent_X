import { db } from '../services/db.service';
import { Integration, IntegrationStatus } from '../types';
import { v4 as uuidv4 } from 'uuid';

export class IntegrationModel {
    /**
     * Get all integrations
     */
    static async findAll(): Promise<Integration[]> {
        const result = await db.query(`
            SELECT * FROM integrations 
            ORDER BY created_at DESC
        `);
        return result.rows;
    }

    /**
     * Get integration by ID
     */
    static async findById(id: string): Promise<Integration | null> {
        const result = await db.query(
            'SELECT * FROM integrations WHERE id = $1',
            [id]
        );
        return result.rows[0] || null;
    }

    /**
     * Create new integration
     */
    static async create(data: Omit<Integration, 'id' | 'createdAt' | 'lastSync'>): Promise<Integration> {
        const id = uuidv4();
        const result = await db.query(
            `INSERT INTO integrations (id, name, type, status, config)
             VALUES ($1, $2, $3, $4, $5)
             RETURNING *`,
            [id, data.name, data.type, data.status, JSON.stringify(data.config)]
        );
        return result.rows[0];
    }

    /**
     * Update integration
     */
    static async update(id: string, data: Partial<Integration>): Promise<Integration | null> {
        const updates: string[] = [];
        const values: any[] = [];
        let paramCount = 1;

        if (data.name !== undefined) {
            updates.push(`name = $${paramCount++}`);
            values.push(data.name);
        }
        if (data.status !== undefined) {
            updates.push(`status = $${paramCount++}`);
            values.push(data.status);
        }
        if (data.config !== undefined) {
            updates.push(`config = $${paramCount++}`);
            values.push(JSON.stringify(data.config));
        }
        if (data.lastSync !== undefined) {
            updates.push(`last_sync = $${paramCount++}`);
            values.push(data.lastSync);
        }

        if (updates.length === 0) {
            return await this.findById(id);
        }

        values.push(id);

        const result = await db.query(
            `UPDATE integrations SET ${updates.join(', ')} WHERE id = $${paramCount} RETURNING *`,
            values
        );

        return result.rows[0] || null;
    }

    /**
     * Delete integration
     */
    static async delete(id: string): Promise<boolean> {
        const result = await db.query('DELETE FROM integrations WHERE id = $1', [id]);
        return (result.rowCount || 0) > 0;
    }
}
