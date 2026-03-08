from database.db_connection import SessionLocal
from api import crud, schemas, models
from api.routes import process_bug_report
import asyncio

async def inject_new_devs():
    db = SessionLocal()
    
    test_cases = [
        ("Nikola_Tesla_2026", "Quantum Encryption Failure", "The encryption module is failing when processing high-entropy keys."),
        ("Ada_Lovelace_AI", "Analytical Engine Overflow", "Recursive calls in the analytical kernel are causing stack overflow."),
        ("Grace_Hopper_Bug", "Nanosecond Delay in Logic", "Observed a 1-nanosecond drift in the timing circuit components.")
    ]
    
    print(f"Injecting {len(test_cases)} bugs with NEW developers...")
    
    for nickname, title, body in test_cases:
        report = schemas.BugCreate(
            title=title,
            body=body,
            priority="high",
            source="github"
        )
        
        match_res = {
            "developer_found": False,
            "status": "NOT_IN_LIST",
            "incoming_name": nickname
        }
        
        print(f"-> Injecting: {title} (Assignee: {nickname})")
        result, error = await process_bug_report(report, db, match_result=match_res)
        if error:
            print(f"   Error: {error}")
        else:
            print(f"   Success! Bug ID: {result.get('bug_id')}")
            
    db.close()

if __name__ == "__main__":
    asyncio.run(inject_new_devs())
