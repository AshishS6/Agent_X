INSERT INTO agents (type, name, description, status, config)
VALUES ('site_scan', 'Site Scan Agent', 'Runs website scans, compliance checks, and KYC site scans.', 'active', '{}')
ON CONFLICT (type) DO NOTHING;
