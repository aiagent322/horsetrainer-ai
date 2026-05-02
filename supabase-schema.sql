-- HorseTrainer.ai — Supabase Schema
-- Run in: https://supabase.com/dashboard/project/ykkfziyxipeuugocwswo/sql

CREATE TABLE IF NOT EXISTS trainers (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name             TEXT NOT NULL,
  business_name    TEXT,
  slug             TEXT UNIQUE NOT NULL,
  email            TEXT,
  phone            TEXT,
  website          TEXT,
  state            TEXT NOT NULL,
  city             TEXT NOT NULL,
  lat              NUMERIC,
  lng              NUMERIC,
  travel_radius    INTEGER,
  online_coaching  BOOLEAN DEFAULT false,
  photo_url        TEXT,
  bio              TEXT,
  years_experience INTEGER,
  disciplines      TEXT[],
  specialties      TEXT[],
  horse_problems   TEXT[],
  rider_levels     TEXT[],
  budget_range     TEXT,
  accepts_dangerous       BOOLEAN DEFAULT false,
  accepts_young_horses    BOOLEAN DEFAULT true,
  certifications   TEXT[],
  associations     TEXT[],
  vip              BOOLEAN DEFAULT false,
  vip_score        INTEGER DEFAULT 0,
  listing_tier     TEXT DEFAULT 'free',
  active           BOOLEAN DEFAULT true,
  created_at       TIMESTAMPTZ DEFAULT now(),
  updated_at       TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS leads (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trainer_id    UUID REFERENCES trainers(id),
  name          TEXT,
  email         TEXT NOT NULL,
  phone         TEXT,
  message       TEXT,
  discipline    TEXT,
  horse_problem TEXT,
  state         TEXT,
  risk_level    TEXT,
  intake_data   JSONB,
  status        TEXT DEFAULT 'new',
  created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS videos (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title         TEXT NOT NULL,
  slug          TEXT UNIQUE NOT NULL,
  youtube_id    TEXT NOT NULL,
  discipline    TEXT[],
  topics        TEXT[],
  skill_level   TEXT,
  description   TEXT,
  duration_sec  INTEGER,
  related_pages TEXT[],
  tags          TEXT[],
  featured      BOOLEAN DEFAULT false,
  active        BOOLEAN DEFAULT true,
  created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS intake_sessions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id    TEXT,
  intake_data   JSONB NOT NULL,
  ai_response   JSONB,
  risk_level    TEXT,
  discipline    TEXT,
  converted     BOOLEAN DEFAULT false,
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- RLS
ALTER TABLE trainers        ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads           ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos          ENABLE ROW LEVEL SECURITY;
ALTER TABLE intake_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read trainers"  ON trainers        FOR SELECT USING (active = true);
CREATE POLICY "Public read videos"    ON videos          FOR SELECT USING (active = true);
CREATE POLICY "Public insert leads"   ON leads           FOR INSERT WITH CHECK (true);
CREATE POLICY "Public insert intake"  ON intake_sessions FOR INSERT WITH CHECK (true);

-- Seed 4 demo trainers (AZ)
INSERT INTO trainers (name, slug, city, state, bio, disciplines, specialties, horse_problems, rider_levels, budget_range, vip, vip_score, listing_tier, online_coaching, accepts_dangerous, active)
VALUES
  ('Wade Callahan', 'wade-callahan', 'Scottsdale', 'AZ', '20+ years starting colts and correcting problem horses across the Southwest. NRHA Professional.', ARRAY['reining','colt_starting'], ARRAY['problem_horse'], ARRAY['bucking','bolting'], ARRAY['intermediate','advanced'], 'mid', true, 90, 'featured', false, true, true),
  ('Shelly Raines', 'shelly-raines', 'Tucson', 'AZ', 'Barrel prospects and youth riders. NBHA member. Building confidence in horse and rider for 15 years.', ARRAY['barrel_racing','trail'], ARRAY['youth_coach'], ARRAY['barn_sour','spooky'], ARRAY['beginner','intermediate'], 'budget', true, 78, 'vip', true, false, true),
  ('R.D. Harmon', 'rd-harmon', 'Prescott', 'AZ', 'Third-generation cowboy. NCHA member. Cutting, cow horse, and ranch horses from the ground up.', ARRAY['cutting','working_cow','ranch'], ARRAY['colt_starting'], ARRAY[]::TEXT[], ARRAY['intermediate','advanced','professional'], 'mid', false, 65, 'basic', false, false, true),
  ('Claire Ashworth', 'claire-ashworth', 'Chandler', 'AZ', 'USEF Certified instructor. Dressage and hunter/jumper from Intro through Third Level. Online video review available.', ARRAY['dressage','hunter_jumper','equitation'], ARRAY['youth_coach','online'], ARRAY['refusing_jumps'], ARRAY['beginner','intermediate','advanced'], 'mid', false, 72, 'vip', true, false, true)
ON CONFLICT (slug) DO NOTHING;
