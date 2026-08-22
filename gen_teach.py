import json

from minah_llm import generate
from minah_llm import generate_toschema

from minah_rag import get_rag_context

from utilities import normalise_filename
from utilities import print_box
from utilities import run_output_through_latex_and_markdown_rendering

from gen_curriculum import ask_user_for_unit_preference, regenerate_lesson_content_file
from minah_classes import Unit


from pathlib import Path

#TODO This is pasted from gen_curriculum, put this function somewhere better
def get_rag_or_warn(unit_folder, rag_question):
    textbook_path = Path(unit_folder) / "textbooks" / "rag"
    if textbook_path.exists():
        return get_rag_context(textbook_path, rag_question)
    #don't warn on the Teach path, just load it if it exists
    # else:
    #     print("No textbooks found for this topic.")
    #     print("Content will be better with a textbook.")
    #     option = input("Press Enter to continue or enter q to quit: ")
    #     if option == "q" or option == "Q":
    #         exit()

def teach(lesson)-> bool:
    
    #print("Starting lesson")
    #start lesson
    history = "###LESSON CONTENT###"
    history += lesson.content
    history += "###END LESSON CONTENT###"
    run_output_through_latex_and_markdown_rendering(lesson.content)
    print_box("You can now ask questions. Enter \"/c\" to continue with lessons.")


    while True:
        question = input()
        if question.strip().lower() == "/preferences":
            new_preference = ask_user_for_unit_preference()
            unit = Unit.load_unit_from_unit_code(lesson.unit_code)
            unit.preferences += new_preference
            unit.save()
            regen = input("Do you want to regenerate this lesson with these preferences? (y/n): ")
            if regen.strip().lower() == "y":
                regenerate_lesson_content_file(lesson)
                #don't show the end of lesson stuff
                return False
            continue
        if question.strip().lower() == "/c":
            break
        elif question.strip() == "":
            continue

        #see if i can move llm warmup and getretriever on another thread that runs while the student goes through the lesson content.
        rag_context = get_rag_or_warn(lesson.unit_folder, question)

        history += f"""###USER QUESTION### 
        {question} 
        ###END USER QUESTION###"""
        prompt = f"""
        You are a teacher and are teaching a lesson titled {lesson.title} with a summary of {lesson.summary}. 
        This is your conversation with the student so far 
        ##BEGIN CONVERSATION HISTORY###
        {history}
        ##END CONVERSATION HISTORY###
        """
        #RAG left out for now
        # To help inform your answer, here is some context from the lesson materials
        # ###BEGIN SOURCE MATERIAL CONTEXT###
        # {rag_context}
        # ###END SOURCE MATERIAL CONTEXT###
        # Some references may be irrelevant. Use only those that directly help answer the student's question.
        # The student has asked the following question {question}.
        # Please answer as a teacher.
        # """

        answer = run_output_through_latex_and_markdown_rendering(generate(prompt, False))
        history += f"""###LLM ANSWER###
        {answer}
        ###END LLM ANSWER###"""      
        print_box("Hope that answered it well. Continue asking questions or enter \"/c\" to continue with lessons.")
        return True