-- Optional seed data (id values auto-generated where BIGSERIAL)
-- Insert commonly used AI models (adjust as needed)
INSERT INTO public.ai_model_configs (
  model_key, display_name, provider, group_name, model_type,
  litellm_prefix, is_enabled, requires_api_key, api_key_env_var, display_order
) VALUES
  ('gpt-4o-mini', 'GPT-4o Mini', 'openai', 'OpenAI', 'openai', 'openai/', TRUE, TRUE, 'OPENAI_API_KEY', 10),
  ('gpt-4o', 'GPT-4o', 'openai', 'OpenAI', 'openai', 'openai/', TRUE, TRUE, 'OPENAI_API_KEY', 20),
  ('claude-3-5-sonnet', 'Claude 3.5 Sonnet', 'anthropic', 'Anthropic', 'litellm', 'anthropic/', TRUE, TRUE, 'ANTHROPIC_API_KEY', 30),
  ('gemini-1.5-pro', 'Gemini 1.5 Pro', 'google', 'Google', 'litellm', 'google/', TRUE, TRUE, 'GOOGLE_API_KEY', 40)
ON CONFLICT (model_key) DO NOTHING;

-- Example agent (remove if not needed)
-- INSERT INTO public.agents (id, name, ai_model, initial_funds, current_funds, max_position_size, status, current_mode)
-- VALUES ('00000000-0000-0000-0000-000000000001', 'Demo Agent', 'gpt-4o-mini', 1000000.00, 1000000.00, 50.00, 'inactive', 'TRADING');
