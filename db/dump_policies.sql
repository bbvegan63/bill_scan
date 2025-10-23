SELECT
    -- Start building the CREATE POLICY statement string
    'CREATE POLICY "' || pol.polname || '"' ||  -- Policy name (quoted)
    ' ON ' || nsp.nspname || '.' || rel.relname || -- Table name (schema.table)
    CASE
        WHEN pol.polpermissive = true THEN ' AS PERMISSIVE'
        ELSE ' AS RESTRICTIVE' -- Although PERMISSIVE is default, being explicit is clear
    END ||
    ' FOR ' || CASE pol.polcmd -- Command type
                WHEN 'r' THEN 'SELECT'
                WHEN 'a' THEN 'INSERT'
                WHEN 'w' THEN 'UPDATE'
                WHEN 'd' THEN 'DELETE'
                WHEN '*' THEN 'ALL' -- Should rarely happen for specific policies, but covers it
                ELSE pol.polcmd::text -- Fallback just in case
            END ||
    -- Determine the TO clause. In Supabase, policies are often for 'authenticated'.
    -- The OID 16479 commonly corresponds to the 'authenticator' role, which the
    -- 'authenticated' pseudo-role effectively executes as. If polroles is null
    -- or empty, it means TO public.
    CASE
        WHEN pol.polroles IS NULL OR array_length(pol.polroles, 1) = 0 THEN ' TO public'
        -- Based on your CSV, [16479] seems to map to 'TO authenticated'.
        -- If you had policies for other specific roles by name, this logic would
        -- need to be more complex (joining pg_roles and aggregating names).
        -- For the common Supabase case with [16479], 'TO authenticated' is appropriate.
        ELSE ' TO authenticated'
    END ||
    -- Add the USING clause if the expression exists
    CASE
        WHEN pg_get_expr(pol.polqual, pol.polrelid) IS NOT NULL THEN ' USING (' || pg_get_expr(pol.polqual, pol.polrelid) || ')'
        ELSE '' -- No USING clause
    END ||
    -- Add the WITH CHECK clause if the expression exists
    CASE
        WHEN pg_get_expr(pol.polwithcheck, pol.polrelid) IS NOT NULL THEN ' WITH CHECK (' || pg_get_expr(pol.polwithcheck, pol.polrelid) || ')'
        ELSE '' -- No WITH CHECK clause
    END ||
    ';' -- Add a semicolon to terminate the statement
AS create_policy_sql -- Alias the generated string column
FROM
    pg_catalog.pg_policy pol
JOIN
    pg_catalog.pg_class rel ON pol.polrelid = rel.oid
JOIN
    pg_catalog.pg_namespace nsp ON rel.relnamespace = nsp.oid
WHERE
    nsp.nspname = 'public'
    AND rel.relname = 'PutYourTableNameHere';