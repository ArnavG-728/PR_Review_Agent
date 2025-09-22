from pr_review_agent.fetch_pr import get_supported_providers

providers = get_supported_providers()
print('Implemented providers:')
for p in providers:
    print(f'- {p["name"]}: {p["implemented"]}')
