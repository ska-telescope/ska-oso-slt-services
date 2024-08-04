CREATE TABLE tab_oda_slt (
    id SERIAL PRIMARY KEY,
    shift_start TIMESTAMP,            
    shift_end TIMESTAMP,              
    shift_operator JSONB,             
    shift_logs JSONB,                 
    media JSONB,                      
    annotations TEXT,                 
    comments TEXT,                    
    created_by VARCHAR(255),          
    created_time TIMESTAMP,           
    last_modified_by VARCHAR(255),    
    last_modified_time TIMESTAMP      
);