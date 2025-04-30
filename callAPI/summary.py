from django.conf import settings
import openai
import logging 
import os
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY
def analyze_call_summary(call):
    """
    Analyze the call's conversation and generate a conclusion using AI.
    """
    try:
        
        print (call.conversation)
        conversation_text=call.conversation
        # # Use OpenAI API to analyze the conversation
        prompt = f"""
                    שפר לי את השיחה הבאה ביני לבין לקוח והפק ממנה את המידע הבא בפורמט קצר ותמציתי (עד 4 מילים):
                        מהי מידת ההתעניינות של הלקוח בשיחה נוספת עם סוכן?
                        אופציה 1: מעוניין, רוצה שיחה
                        אופציה 2: לא מעוניין
                        אופציה 3: לא נאמר
                        במידה והלקוח מעוניין – מתי הוא רוצה שיתקשרו אליו?
                        בוקר / צהריים / ערב
                                    """
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                    {"role": "system", "content": prompt},
                    #  {"role": "assistant", "content":question},
                    {"role": "user", "content": str(conversation_text)},
                ],
            max_tokens=50,
            temperature=0.7,
        )
        
        # Extract the conclusion from the response
        conclusion = response.choices[0].message.content.strip()
        print(conclusion)
        return conclusion
    except Exception as e:
        logger.error(f"Error analyzing call summary: {e}")
        return "Unable to generate a conclusion."