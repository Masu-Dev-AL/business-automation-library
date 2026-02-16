--
-- PostgreSQL database dump
--

-- Dumped from database version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: data_quality_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.data_quality_log (
    log_id integer NOT NULL,
    check_name character varying(100),
    check_date timestamp without time zone,
    status character varying(20),
    records_checked integer,
    records_failed integer,
    details text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.data_quality_log OWNER TO postgres;

--
-- Name: data_quality_log_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.data_quality_log_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.data_quality_log_log_id_seq OWNER TO postgres;

--
-- Name: data_quality_log_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.data_quality_log_log_id_seq OWNED BY public.data_quality_log.log_id;


--
-- Name: dim_customers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dim_customers (
    customer_id integer NOT NULL,
    woo_customer_id integer,
    email character varying(255),
    first_name character varying(100),
    last_name character varying(100),
    segment character varying(50) DEFAULT 'Regular'::character varying,
    lifetime_value numeric(12,2) DEFAULT 0,
    total_orders integer DEFAULT 0,
    customer_since date,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.dim_customers OWNER TO postgres;

--
-- Name: TABLE dim_customers; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.dim_customers IS 'Customer dimension table for customer analytics';


--
-- Name: dim_customers_customer_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dim_customers_customer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dim_customers_customer_id_seq OWNER TO postgres;

--
-- Name: dim_customers_customer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dim_customers_customer_id_seq OWNED BY public.dim_customers.customer_id;


--
-- Name: dim_date; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dim_date (
    date_id integer NOT NULL,
    full_date date NOT NULL,
    year integer,
    quarter integer,
    month integer,
    month_name character varying(20),
    week integer,
    day_of_week integer,
    day_name character varying(20),
    is_weekend boolean,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.dim_date OWNER TO postgres;

--
-- Name: TABLE dim_date; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.dim_date IS 'Date dimension for time-based analysis';


--
-- Name: dim_date_date_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dim_date_date_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dim_date_date_id_seq OWNER TO postgres;

--
-- Name: dim_date_date_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dim_date_date_id_seq OWNED BY public.dim_date.date_id;


--
-- Name: dim_products; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dim_products (
    product_id integer NOT NULL,
    woo_product_id integer,
    sku character varying(100),
    product_name character varying(255) NOT NULL,
    category character varying(100),
    cost_price numeric(10,2),
    sell_price numeric(10,2),
    reorder_point integer DEFAULT 10,
    reorder_quantity integer DEFAULT 50,
    safety_stock integer DEFAULT 5,
    supplier_id integer,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.dim_products OWNER TO postgres;

--
-- Name: TABLE dim_products; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.dim_products IS 'Product dimension table containing product attributes';


--
-- Name: dim_products_product_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dim_products_product_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dim_products_product_id_seq OWNER TO postgres;

--
-- Name: dim_products_product_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dim_products_product_id_seq OWNED BY public.dim_products.product_id;


--
-- Name: dim_suppliers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dim_suppliers (
    supplier_id integer NOT NULL,
    supplier_name character varying(255) NOT NULL,
    contact_email character varying(255),
    contact_phone character varying(50),
    lead_time_days integer DEFAULT 7,
    reliability_score numeric(3,2) DEFAULT 0.95,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.dim_suppliers OWNER TO postgres;

--
-- Name: TABLE dim_suppliers; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.dim_suppliers IS 'Supplier dimension for inventory management';


--
-- Name: dim_suppliers_supplier_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dim_suppliers_supplier_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dim_suppliers_supplier_id_seq OWNER TO postgres;

--
-- Name: dim_suppliers_supplier_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dim_suppliers_supplier_id_seq OWNED BY public.dim_suppliers.supplier_id;


--
-- Name: etl_run_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.etl_run_history (
    run_id integer NOT NULL,
    run_type character varying(50),
    start_time timestamp without time zone,
    end_time timestamp without time zone,
    status character varying(20),
    records_processed integer,
    error_message text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.etl_run_history OWNER TO postgres;

--
-- Name: etl_run_history_run_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.etl_run_history_run_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.etl_run_history_run_id_seq OWNER TO postgres;

--
-- Name: etl_run_history_run_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.etl_run_history_run_id_seq OWNED BY public.etl_run_history.run_id;


--
-- Name: fact_inventory_movements; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fact_inventory_movements (
    movement_id integer NOT NULL,
    product_id integer,
    date_id integer,
    movement_date timestamp without time zone,
    movement_type character varying(50),
    quantity integer,
    reason character varying(255),
    reference_id character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.fact_inventory_movements OWNER TO postgres;

--
-- Name: TABLE fact_inventory_movements; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.fact_inventory_movements IS 'Inventory movement transactions';


--
-- Name: fact_inventory_movements_movement_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fact_inventory_movements_movement_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fact_inventory_movements_movement_id_seq OWNER TO postgres;

--
-- Name: fact_inventory_movements_movement_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fact_inventory_movements_movement_id_seq OWNED BY public.fact_inventory_movements.movement_id;


--
-- Name: fact_inventory_snapshots; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fact_inventory_snapshots (
    snapshot_id integer NOT NULL,
    product_id integer,
    date_id integer,
    snapshot_date date,
    quantity_on_hand integer,
    quantity_allocated integer DEFAULT 0,
    quantity_available integer,
    reorder_needed boolean DEFAULT false,
    days_of_inventory numeric(10,2),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.fact_inventory_snapshots OWNER TO postgres;

--
-- Name: TABLE fact_inventory_snapshots; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.fact_inventory_snapshots IS 'Daily inventory level snapshots';


--
-- Name: fact_inventory_snapshots_snapshot_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fact_inventory_snapshots_snapshot_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fact_inventory_snapshots_snapshot_id_seq OWNER TO postgres;

--
-- Name: fact_inventory_snapshots_snapshot_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fact_inventory_snapshots_snapshot_id_seq OWNED BY public.fact_inventory_snapshots.snapshot_id;


--
-- Name: fact_order_items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fact_order_items (
    order_item_id integer NOT NULL,
    order_fact_id integer,
    product_id integer,
    quantity integer,
    unit_price numeric(10,2),
    line_total numeric(12,2),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.fact_order_items OWNER TO postgres;

--
-- Name: TABLE fact_order_items; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.fact_order_items IS 'Order line items bridge table';


--
-- Name: fact_order_items_order_item_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fact_order_items_order_item_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fact_order_items_order_item_id_seq OWNER TO postgres;

--
-- Name: fact_order_items_order_item_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fact_order_items_order_item_id_seq OWNED BY public.fact_order_items.order_item_id;


--
-- Name: fact_orders; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fact_orders (
    order_fact_id integer NOT NULL,
    woo_order_id integer,
    customer_id integer,
    date_id integer,
    order_date timestamp without time zone,
    status character varying(50),
    total_amount numeric(12,2),
    item_count integer,
    fulfillment_time_hours integer,
    shipping_cost numeric(10,2),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.fact_orders OWNER TO postgres;

--
-- Name: TABLE fact_orders; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.fact_orders IS 'Order fact table containing order transactions';


--
-- Name: fact_orders_order_fact_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fact_orders_order_fact_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fact_orders_order_fact_id_seq OWNER TO postgres;

--
-- Name: fact_orders_order_fact_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fact_orders_order_fact_id_seq OWNED BY public.fact_orders.order_fact_id;


--
-- Name: inventory_alerts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.inventory_alerts (
    alert_id integer NOT NULL,
    product_id integer,
    alert_type character varying(50),
    alert_date timestamp without time zone,
    current_quantity integer,
    threshold_quantity integer,
    is_resolved boolean DEFAULT false,
    resolved_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.inventory_alerts OWNER TO postgres;

--
-- Name: inventory_alerts_alert_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.inventory_alerts_alert_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.inventory_alerts_alert_id_seq OWNER TO postgres;

--
-- Name: inventory_alerts_alert_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.inventory_alerts_alert_id_seq OWNED BY public.inventory_alerts.alert_id;


--
-- Name: vw_current_inventory; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.vw_current_inventory AS
 SELECT p.product_id,
    p.woo_product_id,
    p.sku,
    p.product_name,
    p.category,
    p.sell_price,
    p.reorder_point,
    p.safety_stock,
    s.quantity_on_hand,
    s.quantity_available,
    s.days_of_inventory,
    s.reorder_needed,
        CASE
            WHEN (s.quantity_on_hand <= p.safety_stock) THEN 'Critical'::text
            WHEN (s.quantity_on_hand <= p.reorder_point) THEN 'Low'::text
            ELSE 'Healthy'::text
        END AS stock_status,
    sup.supplier_name,
    sup.lead_time_days
   FROM ((public.dim_products p
     LEFT JOIN public.fact_inventory_snapshots s ON (((p.product_id = s.product_id) AND (s.snapshot_date = (SELECT max(snapshot_date) FROM public.fact_inventory_snapshots)))))
     LEFT JOIN public.dim_suppliers sup ON ((p.supplier_id = sup.supplier_id)))
  WHERE (p.is_active = true);


ALTER VIEW public.vw_current_inventory OWNER TO postgres;

--
-- Name: vw_daily_orders; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.vw_daily_orders AS
 SELECT d.full_date,
    d.day_name,
    d.is_weekend,
    count(DISTINCT o.woo_order_id) AS order_count,
    sum(o.total_amount) AS total_revenue,
    avg(o.total_amount) AS avg_order_value,
    sum(o.item_count) AS total_items
   FROM (public.dim_date d
     LEFT JOIN public.fact_orders o ON ((d.date_id = o.date_id)))
  WHERE (d.full_date >= (CURRENT_DATE - 90))
  GROUP BY d.date_id, d.full_date, d.day_name, d.is_weekend
  ORDER BY d.full_date DESC;


ALTER VIEW public.vw_daily_orders OWNER TO postgres;

--
-- Name: vw_product_performance; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.vw_product_performance AS
 SELECT p.product_id,
    p.product_name,
    p.category,
    p.sell_price,
    COALESCE(sum(oi.quantity), (0)::bigint) AS units_sold_30d,
    COALESCE(sum(oi.line_total), (0)::numeric) AS revenue_30d,
    count(DISTINCT o.order_fact_id) AS order_count_30d
   FROM ((public.dim_products p
     LEFT JOIN public.fact_order_items oi ON ((p.product_id = oi.product_id)))
     LEFT JOIN public.fact_orders o ON (((oi.order_fact_id = o.order_fact_id) AND (o.order_date >= (CURRENT_DATE - 30)))))
  WHERE (p.is_active = true)
  GROUP BY p.product_id, p.product_name, p.category, p.sell_price
  ORDER BY COALESCE(sum(oi.line_total), (0)::numeric) DESC;


ALTER VIEW public.vw_product_performance OWNER TO postgres;

--
-- Name: data_quality_log log_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.data_quality_log ALTER COLUMN log_id SET DEFAULT nextval('public.data_quality_log_log_id_seq'::regclass);


--
-- Name: dim_customers customer_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dim_customers ALTER COLUMN customer_id SET DEFAULT nextval('public.dim_customers_customer_id_seq'::regclass);


--
-- Name: dim_date date_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dim_date ALTER COLUMN date_id SET DEFAULT nextval('public.dim_date_date_id_seq'::regclass);


--
-- Name: dim_products product_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dim_products ALTER COLUMN product_id SET DEFAULT nextval('public.dim_products_product_id_seq'::regclass);


--
-- Name: dim_suppliers supplier_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dim_suppliers ALTER COLUMN supplier_id SET DEFAULT nextval('public.dim_suppliers_supplier_id_seq'::regclass);


--
-- Name: etl_run_history run_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.etl_run_history ALTER COLUMN run_id SET DEFAULT nextval('public.etl_run_history_run_id_seq'::regclass);


--
-- Name: fact_inventory_movements movement_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_inventory_movements ALTER COLUMN movement_id SET DEFAULT nextval('public.fact_inventory_movements_movement_id_seq'::regclass);


--
-- Name: fact_inventory_snapshots snapshot_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_inventory_snapshots ALTER COLUMN snapshot_id SET DEFAULT nextval('public.fact_inventory_snapshots_snapshot_id_seq'::regclass);


--
-- Name: fact_order_items order_item_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_order_items ALTER COLUMN order_item_id SET DEFAULT nextval('public.fact_order_items_order_item_id_seq'::regclass);


--
-- Name: fact_orders order_fact_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_orders ALTER COLUMN order_fact_id SET DEFAULT nextval('public.fact_orders_order_fact_id_seq'::regclass);


--
-- Name: inventory_alerts alert_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_alerts ALTER COLUMN alert_id SET DEFAULT nextval('public.inventory_alerts_alert_id_seq'::regclass);


--
-- Name: data_quality_log data_quality_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.data_quality_log
    ADD CONSTRAINT data_quality_log_pkey PRIMARY KEY (log_id);


--
-- Name: dim_customers dim_customers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dim_customers
    ADD CONSTRAINT dim_customers_pkey PRIMARY KEY (customer_id);


--
-- Name: dim_customers dim_customers_woo_customer_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dim_customers
    ADD CONSTRAINT dim_customers_woo_customer_id_key UNIQUE (woo_customer_id);


--
-- Name: dim_date dim_date_full_date_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dim_date
    ADD CONSTRAINT dim_date_full_date_key UNIQUE (full_date);


--
-- Name: dim_date dim_date_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dim_date
    ADD CONSTRAINT dim_date_pkey PRIMARY KEY (date_id);


--
-- Name: dim_products dim_products_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dim_products
    ADD CONSTRAINT dim_products_pkey PRIMARY KEY (product_id);


--
-- Name: dim_products dim_products_woo_product_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dim_products
    ADD CONSTRAINT dim_products_woo_product_id_key UNIQUE (woo_product_id);


--
-- Name: dim_suppliers dim_suppliers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dim_suppliers
    ADD CONSTRAINT dim_suppliers_pkey PRIMARY KEY (supplier_id);


--
-- Name: etl_run_history etl_run_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.etl_run_history
    ADD CONSTRAINT etl_run_history_pkey PRIMARY KEY (run_id);


--
-- Name: fact_inventory_movements fact_inventory_movements_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_inventory_movements
    ADD CONSTRAINT fact_inventory_movements_pkey PRIMARY KEY (movement_id);


--
-- Name: fact_inventory_snapshots fact_inventory_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_inventory_snapshots
    ADD CONSTRAINT fact_inventory_snapshots_pkey PRIMARY KEY (snapshot_id);


--
-- Name: fact_inventory_snapshots fact_inventory_snapshots_product_id_snapshot_date_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_inventory_snapshots
    ADD CONSTRAINT fact_inventory_snapshots_product_id_snapshot_date_key UNIQUE (product_id, snapshot_date);


--
-- Name: fact_order_items fact_order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_order_items
    ADD CONSTRAINT fact_order_items_pkey PRIMARY KEY (order_item_id);


--
-- Name: fact_orders fact_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_orders
    ADD CONSTRAINT fact_orders_pkey PRIMARY KEY (order_fact_id);


--
-- Name: fact_orders fact_orders_woo_order_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_orders
    ADD CONSTRAINT fact_orders_woo_order_id_key UNIQUE (woo_order_id);


--
-- Name: inventory_alerts inventory_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_alerts
    ADD CONSTRAINT inventory_alerts_pkey PRIMARY KEY (alert_id);


--
-- Name: idx_alerts_product; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_alerts_product ON public.inventory_alerts USING btree (product_id);


--
-- Name: idx_alerts_resolved; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_alerts_resolved ON public.inventory_alerts USING btree (is_resolved);


--
-- Name: idx_alerts_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_alerts_type ON public.inventory_alerts USING btree (alert_type);


--
-- Name: idx_inventory_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_inventory_date ON public.fact_inventory_snapshots USING btree (snapshot_date);


--
-- Name: idx_inventory_product; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_inventory_product ON public.fact_inventory_snapshots USING btree (product_id);


--
-- Name: idx_movements_product; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_movements_product ON public.fact_inventory_movements USING btree (product_id);


--
-- Name: idx_movements_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_movements_type ON public.fact_inventory_movements USING btree (movement_type);


--
-- Name: idx_orders_customer; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_orders_customer ON public.fact_orders USING btree (customer_id);


--
-- Name: idx_orders_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_orders_date ON public.fact_orders USING btree (date_id);


--
-- Name: idx_orders_order_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_orders_order_date ON public.fact_orders USING btree (order_date);


--
-- Name: idx_orders_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_orders_status ON public.fact_orders USING btree (status);


--
-- Name: idx_products_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_category ON public.dim_products USING btree (category);


--
-- Name: idx_products_sku; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_sku ON public.dim_products USING btree (sku);


--
-- Name: dim_products dim_products_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dim_products
    ADD CONSTRAINT dim_products_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.dim_suppliers(supplier_id);


--
-- Name: fact_inventory_movements fact_inventory_movements_date_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_inventory_movements
    ADD CONSTRAINT fact_inventory_movements_date_id_fkey FOREIGN KEY (date_id) REFERENCES public.dim_date(date_id);


--
-- Name: fact_inventory_movements fact_inventory_movements_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_inventory_movements
    ADD CONSTRAINT fact_inventory_movements_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.dim_products(product_id);


--
-- Name: fact_inventory_snapshots fact_inventory_snapshots_date_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_inventory_snapshots
    ADD CONSTRAINT fact_inventory_snapshots_date_id_fkey FOREIGN KEY (date_id) REFERENCES public.dim_date(date_id);


--
-- Name: fact_inventory_snapshots fact_inventory_snapshots_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_inventory_snapshots
    ADD CONSTRAINT fact_inventory_snapshots_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.dim_products(product_id);


--
-- Name: fact_order_items fact_order_items_order_fact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_order_items
    ADD CONSTRAINT fact_order_items_order_fact_id_fkey FOREIGN KEY (order_fact_id) REFERENCES public.fact_orders(order_fact_id);


--
-- Name: fact_order_items fact_order_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_order_items
    ADD CONSTRAINT fact_order_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.dim_products(product_id);


--
-- Name: fact_orders fact_orders_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_orders
    ADD CONSTRAINT fact_orders_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.dim_customers(customer_id);


--
-- Name: fact_orders fact_orders_date_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_orders
    ADD CONSTRAINT fact_orders_date_id_fkey FOREIGN KEY (date_id) REFERENCES public.dim_date(date_id);


--
-- Name: inventory_alerts inventory_alerts_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_alerts
    ADD CONSTRAINT inventory_alerts_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.dim_products(product_id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT ALL ON SCHEMA public TO n8n_user;


--
-- Name: TABLE data_quality_log; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.data_quality_log TO n8n_user;


--
-- Name: SEQUENCE data_quality_log_log_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.data_quality_log_log_id_seq TO n8n_user;


--
-- Name: TABLE dim_customers; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.dim_customers TO n8n_user;


--
-- Name: SEQUENCE dim_customers_customer_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.dim_customers_customer_id_seq TO n8n_user;


--
-- Name: TABLE dim_date; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.dim_date TO n8n_user;


--
-- Name: SEQUENCE dim_date_date_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.dim_date_date_id_seq TO n8n_user;


--
-- Name: TABLE dim_products; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.dim_products TO n8n_user;


--
-- Name: SEQUENCE dim_products_product_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.dim_products_product_id_seq TO n8n_user;


--
-- Name: TABLE dim_suppliers; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.dim_suppliers TO n8n_user;


--
-- Name: SEQUENCE dim_suppliers_supplier_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.dim_suppliers_supplier_id_seq TO n8n_user;


--
-- Name: TABLE etl_run_history; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.etl_run_history TO n8n_user;


--
-- Name: SEQUENCE etl_run_history_run_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.etl_run_history_run_id_seq TO n8n_user;


--
-- Name: TABLE fact_inventory_movements; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.fact_inventory_movements TO n8n_user;


--
-- Name: SEQUENCE fact_inventory_movements_movement_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.fact_inventory_movements_movement_id_seq TO n8n_user;


--
-- Name: TABLE fact_inventory_snapshots; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.fact_inventory_snapshots TO n8n_user;


--
-- Name: SEQUENCE fact_inventory_snapshots_snapshot_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.fact_inventory_snapshots_snapshot_id_seq TO n8n_user;


--
-- Name: TABLE fact_order_items; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.fact_order_items TO n8n_user;


--
-- Name: SEQUENCE fact_order_items_order_item_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.fact_order_items_order_item_id_seq TO n8n_user;


--
-- Name: TABLE fact_orders; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.fact_orders TO n8n_user;


--
-- Name: SEQUENCE fact_orders_order_fact_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.fact_orders_order_fact_id_seq TO n8n_user;


--
-- Name: TABLE inventory_alerts; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.inventory_alerts TO n8n_user;


--
-- Name: SEQUENCE inventory_alerts_alert_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.inventory_alerts_alert_id_seq TO n8n_user;


--
-- Name: TABLE vw_current_inventory; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.vw_current_inventory TO n8n_user;


--
-- Name: TABLE vw_daily_orders; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.vw_daily_orders TO n8n_user;


--
-- Name: TABLE vw_product_performance; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.vw_product_performance TO n8n_user;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO n8n_user;


--
-- PostgreSQL database dump complete
--


