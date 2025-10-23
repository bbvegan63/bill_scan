| tablename           | policyname                                 | permissive | roles                        | cmd    | qual                   | with_check |
| ------------------- | ------------------------------------------ | ---------- | ---------------------------- | ------ | ---------------------- | ---------- |
| document            | Enable insert for authenticated users only | PERMISSIVE | {authenticated,landlord_dev} | INSERT | null                   | true       |
| document            | Enable read access for all users           | PERMISSIVE | {public}                     | SELECT | true                   | null       |
| expense             | Enable insert for authenticated users only | PERMISSIVE | {authenticated,landlord_dev} | INSERT | null                   | true       |
| expense             | Enable read access for all users           | PERMISSIVE | {public}                     | SELECT | true                   | null       |
| lease               | Enable insert for authenticated users only | PERMISSIVE | {authenticated,landlord_dev} | INSERT | null                   | true       |
| lease               | Enable read access for all users           | PERMISSIVE | {public}                     | SELECT | true                   | null       |
| maintenance_request | Enable insert for authenticated users only | PERMISSIVE | {authenticated,landlord_dev} | INSERT | null                   | true       |
| maintenance_request | Enable read access for all users           | PERMISSIVE | {public}                     | SELECT | true                   | null       |
| payment             | Enable insert for authenticated users only | PERMISSIVE | {authenticated,landlord_dev} | INSERT | null                   | true       |
| payment             | Enable read access for all users           | PERMISSIVE | {public}                     | SELECT | true                   | null       |
| property            | Enable insert for authenticated users only | PERMISSIVE | {authenticated,landlord_dev} | INSERT | null                   | true       |
| property            | Enable read access for all users           | PERMISSIVE | {public}                     | SELECT | true                   | null       |
| tenant              | Enable insert for authenticated users only | PERMISSIVE | {authenticated,landlord_dev} | INSERT | null                   | true       |
| tenant              | Users can delete own tenants               | PERMISSIVE | {public}                     | DELETE | (auth.uid() = user_id) | null       |
| tenant              | Users can update own tenants               | PERMISSIVE | {public}                     | UPDATE | (auth.uid() = user_id) | null       |
| tenant              | Users can view own tenants                 | PERMISSIVE | {public}                     | SELECT | (auth.uid() = user_id) | null       |
| utility             | Enable insert for authenticated users only | PERMISSIVE | {authenticated}              | INSERT | null                   | true       |
| utility             | Enable read access for all users           | PERMISSIVE | {public}                     | SELECT | true                   | null       |
| workspace           | Enable insert for authenticated users only | PERMISSIVE | {authenticated,landlord_dev} | INSERT | null                   | true       |
| workspace           | Enable read access for all users           | PERMISSIVE | {public}                     | SELECT | true                   | null       |

| document                                                                                                                          |
| ------------------------------------------------------------------------------------------------------------------------------------------ |
| CREATE POLICY "Enable insert for authenticated users only" ON public.document AS PERMISSIVE FOR INSERT TO authenticated WITH CHECK (true); |
| CREATE POLICY "Enable read access for all users" ON public.document AS PERMISSIVE FOR SELECT TO authenticated USING (true);                |

| expense                                                                                                                         |
| ----------------------------------------------------------------------------------------------------------------------------------------- |
| CREATE POLICY "Enable insert for authenticated users only" ON public.expense AS PERMISSIVE FOR INSERT TO authenticated WITH CHECK (true); |
| CREATE POLICY "Enable read access for all users" ON public.expense AS PERMISSIVE FOR SELECT TO authenticated USING (true);                |

| lease                                                                                                                       |
| --------------------------------------------------------------------------------------------------------------------------------------- |
| CREATE POLICY "Enable insert for authenticated users only" ON public.lease AS PERMISSIVE FOR INSERT TO authenticated WITH CHECK (true); |
| CREATE POLICY "Enable read access for all users" ON public.lease AS PERMISSIVE FOR SELECT TO authenticated USING (true);                |

| maintenance_request                                                                                                                                     |
| ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| CREATE POLICY "Enable insert for authenticated users only" ON public.maintenance_request AS PERMISSIVE FOR INSERT TO authenticated WITH CHECK (true); |
| CREATE POLICY "Enable read access for all users" ON public.maintenance_request AS PERMISSIVE FOR SELECT TO authenticated USING (true);                |

| payment                                                                                                                         |
| ----------------------------------------------------------------------------------------------------------------------------------------- |
| CREATE POLICY "Enable insert for authenticated users only" ON public.payment AS PERMISSIVE FOR INSERT TO authenticated WITH CHECK (true); |
| CREATE POLICY "Enable read access for all users" ON public.payment AS PERMISSIVE FOR SELECT TO authenticated USING (true);                |

| property                                                                                                                          |
| ------------------------------------------------------------------------------------------------------------------------------------------ |
| CREATE POLICY "Enable insert for authenticated users only" ON public.property AS PERMISSIVE FOR INSERT TO authenticated WITH CHECK (true); |
| CREATE POLICY "Enable read access for all users" ON public.property AS PERMISSIVE FOR SELECT TO authenticated USING (true);                |

| tenant                                                                                                                        |
| ---------------------------------------------------------------------------------------------------------------------------------------- |
| CREATE POLICY "Enable insert for authenticated users only" ON public.tenant AS PERMISSIVE FOR INSERT TO authenticated WITH CHECK (true); |
| CREATE POLICY "Users can delete own tenants" ON public.tenant AS PERMISSIVE FOR DELETE TO authenticated USING ((auth.uid() = user_id));  |
| CREATE POLICY "Users can update own tenants" ON public.tenant AS PERMISSIVE FOR UPDATE TO authenticated USING ((auth.uid() = user_id));  |
| CREATE POLICY "Users can view own tenants" ON public.tenant AS PERMISSIVE FOR SELECT TO authenticated USING ((auth.uid() = user_id));    |

| utility                                                                                                                         |
| ----------------------------------------------------------------------------------------------------------------------------------------- |
| CREATE POLICY "Enable insert for authenticated users only" ON public.utility AS PERMISSIVE FOR INSERT TO authenticated WITH CHECK (true); |
| CREATE POLICY "Enable read access for all users" ON public.utility AS PERMISSIVE FOR SELECT TO authenticated USING (true);                |

| workspace                                                                                                                           |
| ------------------------------------------------------------------------------------------------------------------------------------------- |
| CREATE POLICY "Enable insert for authenticated users only" ON public.workspace AS PERMISSIVE FOR INSERT TO authenticated WITH CHECK (true); |
| CREATE POLICY "Enable read access for all users" ON public.workspace AS PERMISSIVE FOR SELECT TO authenticated USING (true);                |