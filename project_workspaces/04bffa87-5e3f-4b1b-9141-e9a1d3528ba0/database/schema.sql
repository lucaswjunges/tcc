CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    role ENUM('user', 'admin') DEFAULT 'user'
);

CREATE TABLE readings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    spread_id UUID REFERENCES spreads(id) ON DELETE SET NULL,
    date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status ENUM('pending', 'completed', 'cancelled') DEFAULT 'pending',
    price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    duration INTERVAL NOT NULL DEFAULT '30 minutes',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE spreads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    card_count INT CHECK (card_count >= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    image_url TEXT,
    position INT CHECK (position >= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE readings_cards (
    reading_id UUID REFERENCES readings(id) ON DELETE CASCADE,
    card_id UUID REFERENCES cards(id) ON DELETE CASCADE,
    position INT NOT NULL,
    interpretation TEXT,
    PRIMARY KEY (reading_id, card_id)
);

CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reading_id UUID REFERENCES readings(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE payment_methods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type ENUM('credit_card', 'paypal', 'bank_transfer') NOT NULL,
    details TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reading_id UUID REFERENCES readings(id) ON DELETE CASCADE,
    scheduled_date TIMESTAMP WITH TIME ZONE NOT NULL,
    status ENUM('pending', 'confirmed', 'completed', 'cancelled') DEFAULT 'pending',
    reminder_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reading_id UUID REFERENCES readings(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_read BOOLEAN DEFAULT FALSE
);

CREATE TABLE faqs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE reading_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    reading_id UUID REFERENCES readings(id) ON DELETE CASCADE,
    status ENUM('pending', 'accepted', 'rejected') DEFAULT 'pending',
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accepted_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE admins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    approved BOOLEAN DEFAULT FALSE,
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_name VARCHAR(100) NOT NULL UNIQUE,
    value TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action TEXT NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    target_table TEXT,
    target_id UUID,
    old_values JSONB,
    new_values JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE deck_customization (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    deck_name VARCHAR(100) NOT NULL,
    card_order TEXT[] NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE reading_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    reading_id UUID REFERENCES readings(id) ON DELETE CASCADE,
    viewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE payment_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reading_id UUID REFERENCES readings(id) ON DELETE CASCADE,
    payment_id TEXT,
    status ENUM('pending', 'success', 'failed') DEFAULT 'pending',
    amount NUMERIC(10,2) NOT NULL,
    transaction_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE deck_sharing (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deck_customization_id UUID REFERENCES deck_customization(id) ON DELETE CASCADE,
    shared_with_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    permissions ENUM('view', 'edit') DEFAULT 'view',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE reading_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    spread_id UUID REFERENCES spreads(id) ON DELETE SET NULL,
    price NUMERIC(10,2) NOT NULL,
    duration INTERVAL NOT NULL DEFAULT '30 minutes',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE template_cards (
    template_id UUID REFERENCES reading_templates(id) ON DELETE CASCADE,
    card_id UUID REFERENCES cards(id) ON DELETE CASCADE,
    interpretation TEXT,
    PRIMARY KEY (template_id, card_id)
);

CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider ENUM('google', 'facebook', 'twitter') NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    value NUMERIC(10,2) NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE content_management (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_type ENUM('blog', 'news', 'article') NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    published BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE user_settings (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    theme ENUM('light', 'dark', 'auto') DEFAULT 'auto',
    language VARCHAR(10) DEFAULT 'en',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (user_id)
);

CREATE TABLE card_customization (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    card_id UUID REFERENCES cards(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    custom_name VARCHAR(100),
    custom_image_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE booking_slots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reading_id UUID REFERENCES readings(id) ON DELETE CASCADE,
    slot_time TIMESTAMP WITH TIME ZONE NOT NULL,
    available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE user_verification (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type ENUM('email', 'phone') NOT NULL,
    status ENUM('pending', 'verified', 'failed') DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE maintenance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    description TEXT NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE rating_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    card_id UUID REFERENCES cards(id) ON DELETE CASCADE,
    rating_avg NUMERIC(3,2),
    review_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE reading_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reading_id UUID REFERENCES readings(id) ON DELETE CASCADE,
    card_id UUID REFERENCES cards(id) ON DELETE CASCADE,
    count INT DEFAULT 0,
    PRIMARY KEY (reading_id, card_id)
);

CREATE TABLE deck_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deck_customization_id UUID REFERENCES deck_customization(id) ON DELETE CASCADE,
    action_type ENUM('create', 'update', 'delete') NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE payment_gateway (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider ENUM('stripe', 'paypal', 'mercadopago') NOT NULL,
    api_key TEXT NOT NULL,
    webhook_secret TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE subscription (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plan_name VARCHAR(100) NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_date TIMESTAMP WITH TIME ZONE,
    status ENUM('active', 'cancelled', 'ended') DEFAULT 'active',
    price NUMERIC(10,2) NOT NULL,
    payment_method_id UUID REFERENCES payment_methods(id) ON DELETE SET NULL
);

CREATE TABLE discount_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    type ENUM('percentage', 'fixed') NOT NULL,
    value NUMERIC(10,2) NOT NULL CHECK (value >= 0),
    max_usage INT CHECK (max_usage >= 0),
    used_count INT DEFAULT 0,
    valid_from TIMESTAMP WITH TIME ZONE,
    valid_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE code_redemption (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    discount_code_id UUID REFERENCES discount_codes(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    redeemed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE card_pack (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price NUMERIC(10,2) NOT NULL,
    cards INT NOT NULL CHECK (cards > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE card_pack_customization (
    pack_id UUID REFERENCES card_pack(id) ON DELETE CASCADE,
    card_id UUID REFERENCES cards(id) ON DELETE CASCADE,
    PRIMARY KEY (pack_id, card_id)
);

CREATE TABLE transaction_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reading_id UUID REFERENCES readings(id) ON DELETE CASCADE,
    amount NUMERIC(10,2) NOT NULL,
    payment_type ENUM('online', 'offline') NOT NULL,
    status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
    transaction_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE user_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE card_pack_purchase (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    pack_id UUID REFERENCES card_pack(id) ON DELETE CASCADE,
    purchased_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE deck_sync (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deck_customization_id UUID REFERENCES deck_customization(id) ON DELETE CASCADE,
    cloud_sync BOOLEAN DEFAULT FALSE,
    last_synced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE reading_scheduling (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    preferred_date DATE,
    preferred_time TIME,
    timezone VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE card_pack_redemption (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pack_id UUID REFERENCES card_pack(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    redeemed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE user_card_association (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    card_id UUID REFERENCES cards(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, card_id)
);

CREATE TABLE reading_card_ranking (
    reading_id UUID REFERENCES readings(id) ON DELETE CASCADE,
    card_id UUID REFERENCES cards(id) ON DELETE CASCADE,
    rank INT NOT NULL,
    PRIMARY KEY (reading_id, card_id)
);

CREATE TABLE deck_sync_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deck_customization_id UUID REFERENCES deck_customization(id) ON DELETE CASCADE,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    changes JSONB
);

CREATE TABLE payment_webhook (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_name VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL,
    signature TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE card_pack_discount (
    pack_id UUID REFERENCES card_pack(id) ON DELETE CASCADE,
    discount_code_id UUID REFERENCES discount_codes(id) ON DELETE CASCADE,
    PRIMARY KEY (pack_id, discount_code_id)
);

CREATE TABLE reading_pack (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price NUMERIC(10,2) NOT NULL,
    duration INTERVAL NOT NULL,
    card_count INT NOT NULL,
    spread_id UUID REFERENCES spreads(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE reading_pack_purchase (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    purchased_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE reading_pack_redemption (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    redeemed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE reading_pack_card (
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    card_id UUID REFERENCES cards(id) ON DELETE CASCADE,
    PRIMARY KEY (pack_id, card_id)
);

CREATE TABLE reading_pack_spread (
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    spread_id UUID REFERENCES spreads(id) ON DELETE CASCADE,
    PRIMARY KEY (pack_id, spread_id)
);

CREATE TABLE reading_pack_price (
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    price NUMERIC(10,2) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    valid_from TIMESTAMP WITH TIME ZONE,
    valid_until TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (pack_id, currency)
);

CREATE TABLE reading_pack_discount (
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    discount_code_id UUID REFERENCES discount_codes(id) ON DELETE CASCADE,
    PRIMARY KEY (pack_id, discount_code_id)
);

CREATE TABLE reading_pack_subscription (
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES subscription(id) ON DELETE CASCADE,
    PRIMARY KEY (pack_id, subscription_id)
);

CREATE TABLE reading_pack_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (pack_id, user_id)
);

CREATE TABLE reading_pack_webhook (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    event_name VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE reading_pack_sync (
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    synced BOOLEAN DEFAULT FALSE,
    last_synced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE reading_pack_card_ranking (
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    card_id UUID REFERENCES cards(id) ON DELETE CASCADE,
    rank INT NOT NULL,
    PRIMARY KEY (pack_id, card_id)
);

CREATE TABLE reading_pack_spread_ranking (
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    spread_id UUID REFERENCES spreads(id) ON DELETE CASCADE,
    rank INT NOT NULL,
    PRIMARY KEY (pack_id, spread_id)
);

CREATE TABLE reading_pack_price_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    currency CHAR(3) NOT NULL,
    old_price NUMERIC(10,2),
    new_price NUMERIC(10,2) NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE reading_pack_discount_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    discount_code_id UUID REFERENCES discount_codes(id) ON DELETE CASCADE,
    old_discount BOOLEAN,
    new_discount BOOLEAN,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE reading_pack_subscription_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES subscription(id) ON DELETE CASCADE,
    old_status ENUM('active', 'cancelled', 'ended'),
    new_status ENUM('active', 'cancelled', 'ended') NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE reading_pack_usage_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    old_count INT,
    new_count INT NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE reading_pack_webhook_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    event_name VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE reading_pack_sync_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    changes JSONB
);

CREATE TABLE reading_pack_card_ranking_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    card_id UUID REFERENCES cards(id) ON DELETE CASCADE,
    old_rank INT,
    new_rank INT NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE reading_pack_spread_ranking_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pack_id UUID REFERENCES reading_pack(id) ON DELETE CASCADE,
    spread_id UUID REFERENCES spreads(id) ON DELETE CASCADE,
    old_rank INT,
    new_rank INT NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMIT;