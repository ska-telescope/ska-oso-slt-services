CREATE TABLE tab_oda_slt (
    id TEXT PRIMARY KEY NOT NULL,
    comments TEXT,
    shift_start TIMESTAMP NOT NULL,
    shift_end TIMESTAMP,
    annotation TEXT,
    created_on TIMESTAMP NOT NULL,
    created_by VARCHAR(255) DEFAULT 'Defaultuser',
    last_modified_on TIMESTAMP NOT NULL,
    last_modified_by VARCHAR(255) DEFAULT 'DefaultUser'
);



CREATE TABLE tab_oda_slt_log (
    id SERIAL PRIMARY KEY NOT NULL,
    slt_ref TEXT REFERENCES tab_oda_slt(id) ON DELETE CASCADE,
    info JSONB NOT NULL,
    source VARCHAR(255) NOT NULL,
    created_on TIMESTAMP NOT NULL,
    created_by VARCHAR(255) DEFAULT 'Defaultuser',
    last_modified_on TIMESTAMP NOT NULL,
    last_modified_by VARCHAR(255) DEFAULT 'DefaultUser'
);



CREATE TABLE tab_oda_slt_image (
    id SERIAL PRIMARY KEY NOT NULL,
    slt_ref TEXT REFERENCES tab_oda_slt(id) ON DELETE CASCADE,
    image_path TEXT NOT NULL,
    created_on TIMESTAMP NOT NULL,
    created_by VARCHAR(255) DEFAULT 'Defaultuser',
    last_modified_on TIMESTAMP NOT NULL,
    last_modified_by VARCHAR(255) DEFAULT 'DefaultUser'
);
