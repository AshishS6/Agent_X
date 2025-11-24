import { db } from '../services/db.service';
import { Agent, AgentType, AgentStatus } from '../types';
import { v4 as uuidv4 } from 'uuid';

export class AgentModel {
    /**
     * Get all agents
     */
    static async findAll(): Promise<Agent[]> {
        const result = await db.query(`
      SELECT * FROM agents 
      ORDER BY created_at DESC
    `);
        return result.rows;
    }

    /**
     * Get agent by ID
     */
    static async findById(id: string): Promise<Agent | null> {
        const result = await db.query(
            'SELECT * FROM agents WHERE id = $1',
            [id]
        );
        return result.rows[0] || null;
    }

    /**
     * Get agent by type
     */
    static async findByType(type: AgentType): Promise<Agent | null> {
        const result = await db.query(
            'SELECT * FROM agents WHERE type = $1',
            [type]
        );
        return result.rows[0] || null;
    }

    /**
     * Create new agent
     */
    static async create(data: Omit<Agent, 'id' | 'createdAt' | 'updatedAt'>): Promise<Agent> {
        const id = uuidv4();
        const result = await db.query(
            `INSERT INTO agents (id, type, name, description, status, config)
       VALUES ($1, $2, $3, $4, $5, $6)
       RETURNING *`,
            [id, data.type, data.name, data.description, data.status, JSON.stringify(data.config)]
        );
        return result.rows[0];
    }

    /**
     * Update agent
     */
    static async update(id: string, data: Partial<Agent>): Promise<Agent | null> {
        const updates: string[] = [];
        const values: any[] = [];
        let paramCount = 1;

        if (data.name !== undefined) {
            updates.push(`name = $${paramCount++}`);
            values.push(data.name);
        }
        if (data.description !== undefined) {
            updates.push(`description = $${paramCount++}`);
            values.push(data.description);
        }
        if (data.status !== undefined) {
            updates.push(`status = $${paramCount++}`);
            values.push(data.status);
        }
        if (data.config !== undefined) {
            updates.push(`config = $${paramCount++}`);
            values.push(JSON.stringify(data.config));
        }

        if (updates.length === 0) {
            return await this.findById(id);
        }

        updates.push(`updated_at = NOW()`);
        values.push(id);

        const result = await db.query(
            `UPDATE agents SET ${updates.join(', ')} WHERE id = $${paramCount} RETURNING *`,
            values
        );

        return result.rows[0] || null;
    }

    /**
     * Delete agent
     */
    static async delete(id: string): Promise<boolean> {
        const result = await db.query('DELETE FROM agents WHERE id = $1', [id]);
        return (result.rowCount || 0) > 0;
    }
}
