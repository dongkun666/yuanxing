import yaml
import json
plan = yaml.safe_load(open(r'E:\元枢法智前端\yuanxing\docs\plans\plan-08-w8-yaml.yaml', encoding='utf-8'))
print('YAML type:', type(plan))
print('YAML keys:', list(plan.keys()) if plan else 'EMPTY')
if plan:
    print('plan keys:', list(plan.get('plan', {}).keys()))
    if 'plan' in plan:
        print('plan.plan type:', type(plan['plan']))
        if 'tasks' in plan['plan']:
            print('tasks count:', len(plan['plan']['tasks']))
            for t in plan['plan']['tasks'][:3]:
                print('  task keys:', list(t.keys())[:5])
        else:
            print('NO tasks key in plan.plan')
            print('plan.plan content:', json.dumps(plan['plan'], ensure_ascii=False)[:500])
