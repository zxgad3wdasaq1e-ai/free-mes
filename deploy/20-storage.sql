-- Use persistent local file storage for a fresh installation.
-- Relative URLs work with the same origin and do not depend on a server IP.
UPDATE infra_file_config
SET name = 'local', storage = 10,
    config = '{"@class":"io.metaxk.framework.file.core.client.local.LocalFileClientConfig","basePath":"/data/uploads","domain":""}'
WHERE id = 18;
