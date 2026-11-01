# Lesson data (learn Spanish)
# type "choice" = multiple choice question
# type "order"  = put the words in the correct order ("extra" = wrong words mixed in)

LESSONS = [
    {
        "name": "Greetings",
        "questions": [
            {"type": "choice", "question": 'What does "Hola" mean?',
             "options": ["Hello", "Goodbye", "Thanks", "Please"], "answer": "Hello"},
            {"type": "choice", "question": 'How do you say "Goodbye"?',
             "options": ["Gracias", "Adiós", "Hola", "Sí"], "answer": "Adiós"},
            {"type": "order", "question": 'Translate: "Good morning"',
             "answer": ["Buenos", "días"], "extra": ["noches"]},
            {"type": "choice", "question": 'What does "Gracias" mean?',
             "options": ["Sorry", "Hello", "Thank you", "Yes"], "answer": "Thank you"},
            {"type": "order", "question": 'Translate: "See you later"',
             "answer": ["Hasta", "luego"], "extra": ["hola", "por"]},
        ],
    },
    {
        "name": "Food",
        "questions": [
            {"type": "choice", "question": 'What does "manzana" mean?',
             "options": ["Banana", "Apple", "Bread", "Milk"], "answer": "Apple"},
            {"type": "choice", "question": 'How do you say "water"?',
             "options": ["Agua", "Leche", "Pan", "Café"], "answer": "Agua"},
            {"type": "order", "question": 'Translate: "I eat bread"',
             "answer": ["Yo", "como", "pan"], "extra": ["agua"]},
            {"type": "choice", "question": 'What does "leche" mean?',
             "options": ["Milk", "Juice", "Egg", "Rice"], "answer": "Milk"},
            {"type": "order", "question": 'Translate: "I drink water"',
             "answer": ["Yo", "bebo", "agua"], "extra": ["pan", "como"]},
        ],
    },
    {
        "name": "Family",
        "questions": [
            {"type": "choice", "question": 'What does "madre" mean?',
             "options": ["Father", "Sister", "Mother", "Brother"], "answer": "Mother"},
            {"type": "choice", "question": 'How do you say "brother"?',
             "options": ["Hermano", "Padre", "Hijo", "Abuelo"], "answer": "Hermano"},
            {"type": "order", "question": 'Translate: "My father is tall"',
             "answer": ["Mi", "padre", "es", "alto"], "extra": ["madre"]},
            {"type": "choice", "question": 'What does "abuela" mean?',
             "options": ["Aunt", "Grandmother", "Daughter", "Cousin"], "answer": "Grandmother"},
            {"type": "order", "question": 'Translate: "I have a sister"',
             "answer": ["Tengo", "una", "hermana"], "extra": ["un", "padre"]},
        ],
    },
]
