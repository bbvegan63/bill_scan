-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.document (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  document_type text,
  title text,
  notes text,
  file_urls ARRAY,
  upload_date text,
  extracted_data text,
  property_id bigint,
  tenant_id bigint,
  lease_id bigint,
  user_id uuid,
  utility_id bigint,
  CONSTRAINT document_pkey PRIMARY KEY (id)
);
CREATE TABLE public.expense (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT expense_pkey PRIMARY KEY (id)
);
CREATE TABLE public.lease (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  property_id bigint,
  tenant_id bigint,
  start_date text,
  end_date text,
  base_amount_per_period text,
  payment_frequency text,
  first_payment_due_date text,
  lease_type text,
  security_deposit text,
  lease_document_urls ARRAY,
  status text,
  notes text,
  extracted_data text,
  user_id uuid,
  CONSTRAINT lease_pkey PRIMARY KEY (id)
);
CREATE TABLE public.maintenance_request (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT maintenance_request_pkey PRIMARY KEY (id)
);
CREATE TABLE public.payment (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT payment_pkey PRIMARY KEY (id)
);
CREATE TABLE public.property (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  address text,
  unit_number text,
  property_type text,
  bedrooms text,
  bathrooms text,
  square_feet text,
  purchase_date text,
  purchase_price text,
  status text,
  photo_url text,
  notes text,
  user_id uuid,
  CONSTRAINT property_pkey PRIMARY KEY (id)
);
CREATE TABLE public.tenant (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  full_name text,
  email text,
  status text,
  phone text,
  notes text,
  documents ARRAY,
  emergency_contact_name text,
  emergency_contact_phone text,
  move_in_date text,
  move_out_date text,
  user_id uuid,
  CONSTRAINT tenant_pkey PRIMARY KEY (id)
);
CREATE TABLE public.users (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  email text,
  email_verified text,
  full_name text,
  role text,
  CONSTRAINT users_pkey PRIMARY KEY (id)
);
CREATE TABLE public.utility (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  account_number text,
  service_type text,
  status text,
  start_date text,
  end_date text,
  notes text,
  property_id bigint,
  tenant_id bigint,
  user_id uuid,
  CONSTRAINT utility_pkey PRIMARY KEY (id)
);
CREATE TABLE public.workspace (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT workspace_pkey PRIMARY KEY (id)
);