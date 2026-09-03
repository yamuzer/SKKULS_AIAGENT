
entities = [
    {
        'id': 'person_001',
        'name': '철수',
        'type': 'Person'
    },
    {
        'id': 'company_001',
        'name': 'ABC 회사',
        'type': 'Company'
    },
    {
        'id': 'city_001',
        'name': '서울',
        'type': 'City'
    },
    {
        'id': 'tech_001',
        'name': 'Python',
        'type': 'Tech'
    }
]

# relation / triple 정의
triples = [
    {
        'subject': '철수',
        'predicate': 'WORK_AT', #관계
        'object': 'ABC 회사'
    },
    {
        'subject': 'ABC 회사',
        'predicate': 'LOCATED_IN',
        'object': '서울'
    },
    {
        'subject': '철수',
        'predicate': 'USES', 
        'object': 'Python'
    }
]

print('\n관계 표현')

for triple in triples:
    print(
        triple['subject'],
        '--',
        triple['predicate'],
        '->',
        triple['object']
    )

# 특정 Entity가 subject인 관계 찾기

target = '철수'

print(f'\n{target}와 관련된 관계')

for triple in triples:
    if triple['subject'] == target:
        print(
        triple['subject'],
        '--',
        triple['predicate'],
        '->',
        triple['object']
    )
