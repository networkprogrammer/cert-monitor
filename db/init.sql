CREATE TABLE IF NOT EXISTS certificates (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(255) NOT NULL,
    expiry_date TIMESTAMP NOT NULL,
    issuer VARCHAR(255) NOT NULL,
    fingerprint VARCHAR(255) NOT NULL,
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='certificates' AND column_name='cert_type'
    ) THEN
        ALTER TABLE certificates ADD COLUMN cert_type VARCHAR(20) NOT NULL DEFAULT 'leaf';
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='certificates' AND column_name='pem_certificate'
    ) THEN
        ALTER TABLE certificates ADD COLUMN pem_certificate TEXT;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(255) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='alerts' AND column_name='fingerprint'
    ) THEN
        ALTER TABLE alerts ADD COLUMN fingerprint VARCHAR(255);
    END IF;
END $$;