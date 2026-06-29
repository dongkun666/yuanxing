import yaml
plan = yaml.safe_load(open(r'E:\元枢法智前端\yuanxing\docs\plans\plan-11-w11-yaml.yaml', encoding='utf-8'))
print('YAML OK, tasks:', len(plan['tasks']))
print('max_concurrency:', plan['plan']['max_concurrency'])
print('max_cycles:', plan['plan']['max_cycles'])
print('depends_on chain:')
for t in plan['tasks']:
    print(f'  {t["id"]} -> {t["depends_on"]} role={t["role"]} assigned={t["assigned_to"]}')
