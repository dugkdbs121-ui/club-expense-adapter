"""정수 원 단위로 합계와 분류별 건수를 계산한다."""


def summarize(records):
    total = 0
    groups = {}
    for record in records:
        category = record["category"]
        amount = record["amount"]
        total += amount
        if category not in groups:
            groups[category] = {"count": 0, "total": 0}
        groups[category]["count"] += 1
        groups[category]["total"] += amount
    categories = []
    for category in sorted(groups):
        categories.append({
            "category": category,
            "count": groups[category]["count"],
            "total": groups[category]["total"],
        })
    return {"count": len(records), "total": total, "categories": categories}
