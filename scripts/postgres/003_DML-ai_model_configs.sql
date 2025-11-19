INSERT INTO public.ai_model_configs (model_key,display_name,provider,group_name,model_type,litellm_prefix,is_enabled,requires_api_key,api_key_env_var,display_order,created_at,updated_at) VALUES
	 ('gpt-4o-mini','OpenAI - GPT-4o mini','OpenAI','OpenAI','openai',NULL,true,true,'OPENAI_API_KEY',10,'2025-10-12 00:46:53.332099+08','2025-10-12 00:46:53.3321+08'),
	 ('gpt-4.1-mini','OpenAI - GPT-4.1 mini','OpenAI','OpenAI','openai',NULL,true,true,'OPENAI_API_KEY',9,'2025-10-12 00:46:53.3321+08','2025-10-12 00:46:53.332101+08'),
	 ('gemini-2.5-pro','Google - Gemini 2.5 Pro','GitHub Copilot','GitHub Copilot','litellm','github_copilot/',true,true,'GITHUB_PERSONAL_ACCESS_TOKEN',7,'2025-10-12 00:46:53.332101+08','2025-10-12 00:46:53.332102+08'),
	 ('gpt-4.1','OpenAI - GPT-4.1','GitHub Copilot','GitHub Copilot','litellm','github_copilot/',true,true,'GITHUB_PERSONAL_ACCESS_TOKEN',3,'2025-10-12 00:46:53.332102+08','2025-10-12 00:46:53.332103+08'),
	 ('gpt-5','OpenAI - GPT-5','GitHub Copilot','GitHub Copilot','litellm','github_copilot/',true,true,'GITHUB_PERSONAL_ACCESS_TOKEN',4,'2025-10-27 01:23:34+08','2025-10-27 01:23:34+08'),
	 ('gpt-5-mini','OpenAI - GPT-5 mini','GitHub Copilot','GitHub Copilot','litellm','github_copilot/',true,true,'GITHUB_PERSONAL_ACCESS_TOKEN',1,'2025-10-27 01:25:03+08','2025-10-27 01:25:03+08'),
	 ('claude-haiku-4.5','Anthropic - Claude Haiku 4.5','GitHub Copilot','GitHub Copilot','litellm','github_copilot/',true,true,'GITHUB_PERSONAL_ACCESS_TOKEN',5,'2025-10-27 01:26:20+08','2025-10-27 01:26:20+08'),
	 ('claude-sonnet-4.5','Anthropic - Claude Sonnet 4.5','GitHub Copilot','GitHub Copilot','litellm','github_copilot/',true,true,'GITHUB_PERSONAL_ACCESS_TOKEN',6,'2025-10-27 01:26:46+08','2025-10-27 01:26:46+08'),
	 ('grok-code-fast-1','xAI - Grok Code Fast 1','GitHub Copilot','GitHub Copilot','litellm','github_copilot/',true,true,'GITHUB_PERSONAL_ACCESS_TOKEN',8,'2025-10-27 01:28:26+08','2025-10-27 01:28:26+08'),
	 ('gpt-4o','OpenAI - GPT-4o','GitHub Copilot','GitHub Copilot','litellm','github_copilot/',true,true,'GITHUB_PERSONAL_ACCESS_TOKEN',2,'2025-10-27 01:34:32+08','2025-10-27 01:34:32+08');
