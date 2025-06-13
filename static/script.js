document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const form = document.getElementById('qcm-form');
    const loadingSection = document.getElementById('loading');
    const resultsSection = document.getElementById('results');
    const questionsContainer = document.getElementById('questions-container');
    const alertContainer = document.getElementById('alert-container');
    const fileUpload = document.getElementById('file-upload');
    const fileName = document.getElementById('file-name');
    const trainingStatus = document.getElementById('training-status');
    const documentList = document.getElementById('document-list');
    const useRagBtn = document.getElementById('use-rag-btn');
    const useTextBtn = document.getElementById('use-text-btn');
    const ragInterface = document.getElementById('rag-interface');
    const textInterface = document.getElementById('text-interface');
    const rawText = document.getElementById('raw-text');
    const paragraphsContainer = document.getElementById('paragraphs-container');
    const paragraphsList = document.getElementById('paragraphs-list');
    const ragQuery = document.getElementById('rag-query');
    const levelSelect = document.getElementById('text-level');
    const difficultySelect = document.getElementById('text-difficulty');
    
    // Selected document path and global variables
    let selectedDocumentPath = 'arabic.pdf';
    let selectedParagraphs = [];
    window.textContent = ''; // Make textContent globally accessible
    
    // Show alert function - make it globally accessible
    window.showAlert = function(message, type) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        
        alertContainer.innerHTML = '';
        alertContainer.appendChild(alert);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
    
    // Handle form submission
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const numQuestions = document.getElementById('num-questions').value;
            const model = document.getElementById('model').value;
            const level = levelSelect ? levelSelect.value : 1;
            const difficulty = difficultySelect ? difficultySelect.value : 'medium';
            
            // Get text from the input
            const text = rawText.value;
            window.textContent = text; // Save for later use in global scope
            
            if (!text) {
                showAlert('يرجى إدخال النص العربي', 'error');
                return;
            }
            
            // If no paragraphs are selected, show an alert
            if (selectedParagraphs.length === 0) {
                showAlert('يرجى اختيار فقرة واحدة على الأقل', 'error');
                return;
            }
            
            // Show loading
            loadingSection.style.display = 'block';
            resultsSection.style.display = 'none';
            
            // Send request to generate QCMs
            fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    num_questions: parseInt(numQuestions),
                    model: model,
                    document_path: selectedDocumentPath,
                    selected_paragraphs: selectedParagraphs,
                    level: parseInt(level),
                    difficulty: difficulty
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.task_id) {
                    checkTaskStatus(data.task_id);
                } else {
                    showAlert('حدث خطأ أثناء إنشاء المهمة', 'error');
                    loadingSection.style.display = 'none';
                }
            })
            .catch(error => {
                showAlert('حدث خطأ: ' + error, 'error');
                loadingSection.style.display = 'none';
            });
        });
    }
    
    // Check task status
    function checkTaskStatus(taskId) {
        fetch(`/status/${taskId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'completed') {
                    // Show results
                    displayResults(data.questions);
                    loadingSection.style.display = 'none';
                    resultsSection.style.display = 'block';
                } else if (data.status === 'error') {
                    showAlert('حدث خطأ: ' + data.error, 'error');
                    loadingSection.style.display = 'none';
                } else {
                    // Check again after 2 seconds
                    setTimeout(() => checkTaskStatus(taskId), 2000);
                }
            })
            .catch(error => {
                showAlert('حدث خطأ أثناء التحقق من حالة المهمة: ' + error, 'error');
                loadingSection.style.display = 'none';
            });
    }
    
    // Display results
    function displayResults(questions) {
        questionsContainer.innerHTML = '';
        
        questions.forEach((question, index) => {
            const questionCard = document.createElement('div');
            questionCard.className = 'question-card';
            questionCard.dataset.index = index;
            
            // Create editable question text
            const questionText = document.createElement('div');
            questionText.className = 'question-text';
            questionText.contentEditable = true;
            questionText.textContent = `${index + 1}. ${question.question}`;
            questionText.dataset.originalText = question.question;
            
            const choicesList = document.createElement('ul');
            choicesList.className = 'choices';
            
            question.choices.forEach((choice, choiceIndex) => {
                const choiceItem = document.createElement('li');
                choiceItem.className = 'choice';
                if (choice === question.correct_answer) {
                    choiceItem.classList.add('correct');
                }
                
                // Create editable choice text
                const choiceText = document.createElement('span');
                choiceText.contentEditable = true;
                choiceText.textContent = choice;
                choiceText.dataset.originalText = choice;
                
                const choiceLabel = document.createElement('span');
                choiceLabel.className = 'choice-label';
                choiceLabel.textContent = `${String.fromCharCode(65 + choiceIndex)}. `;
                
                // Add radio button for selecting correct answer
                const radioBtn = document.createElement('input');
                radioBtn.type = 'radio';
                radioBtn.name = `correct-answer-${index}`;
                radioBtn.className = 'correct-answer-radio';
                radioBtn.checked = choice === question.correct_answer;
                radioBtn.addEventListener('change', function() {
                    // Remove correct class from all choices in this question
                    choicesList.querySelectorAll('.choice').forEach(c => c.classList.remove('correct'));
                    // Add correct class to this choice
                    choiceItem.classList.add('correct');
                });
                
                choiceItem.appendChild(radioBtn);
                choiceItem.appendChild(choiceLabel);
                choiceItem.appendChild(choiceText);
                
                choicesList.appendChild(choiceItem);
            });
            
            // Add action buttons (save, delete, and improve)
            const actionButtons = document.createElement('div');
            actionButtons.className = 'question-actions';
            
            const saveButton = document.createElement('button');
            saveButton.className = 'action-btn save-btn';
            saveButton.innerHTML = '<i class="fas fa-save"></i>';
            saveButton.title = 'حفظ السؤال';
            saveButton.onclick = function() { saveQuestion(index); };
            
            const deleteButton = document.createElement('button');
            deleteButton.className = 'action-btn delete-btn';
            deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
            deleteButton.title = 'حذف السؤال';
            deleteButton.onclick = function() { deleteQuestion(index); };
            
            const improveButton = document.createElement('button');
            improveButton.className = 'action-btn improve-btn';
            improveButton.innerHTML = '<i class="fas fa-magic"></i>';
            improveButton.title = 'تحسين السؤال';
            improveButton.onclick = function() { improveQuestion(index); };
            
            actionButtons.appendChild(saveButton);
            actionButtons.appendChild(deleteButton);
            actionButtons.appendChild(improveButton);
            
            questionCard.appendChild(questionText);
            questionCard.appendChild(choicesList);
            questionCard.appendChild(actionButtons);
            questionsContainer.appendChild(questionCard);
        });
    }
    
    // Save a single question
    function saveQuestion(index) {
        const card = document.querySelector(`.question-card[data-index="${index}"]`);
        if (!card) return;
        
        const questionTextEl = card.querySelector('.question-text');
        const questionText = questionTextEl.textContent.substring(questionTextEl.textContent.indexOf('. ') + 2);
        
        const choices = [];
        const choiceElements = card.querySelectorAll('.choice');
        let correctAnswer = '';
        
        choiceElements.forEach(choice => {
            const choiceText = choice.querySelector('span[contenteditable="true"]').textContent;
            choices.push(choiceText);
            
            if (choice.classList.contains('correct')) {
                correctAnswer = choiceText;
            }
        });
        
        const question = {
            question: questionText,
            correct_answer: correctAnswer,
            choices: choices
        };
        
        // Save to MongoDB via API
        fetch('/save-question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(question)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('تم حفظ السؤال بنجاح', 'success');
            } else {
                showAlert('حدث خطأ أثناء حفظ السؤال: ' + data.message, 'error');
            }
        })
        .catch(error => {
            showAlert('حدث خطأ أثناء حفظ السؤال: ' + error, 'error');
        });
    }
    
    // Delete a question
    function deleteQuestion(index) {
        const card = document.querySelector(`.question-card[data-index="${index}"]`);
        if (card) {
            card.remove();
            showAlert('تم حذف السؤال', 'success');
        }
    }
    
    // Export to JSON
    const exportJsonBtn = document.getElementById('export-json');
    if (exportJsonBtn) {
        exportJsonBtn.addEventListener('click', function() {
            const questions = [];
            document.querySelectorAll('.question-card').forEach((card) => {
                const questionTextEl = card.querySelector('.question-text');
                const questionText = questionTextEl.textContent.substring(questionTextEl.textContent.indexOf('. ') + 2);
                
                const choices = [];
                const choiceElements = card.querySelectorAll('.choice');
                let correctAnswer = '';
                
                choiceElements.forEach(choice => {
                    const choiceText = choice.querySelector('span[contenteditable="true"]').textContent;
                    choices.push(choiceText);
                    
                    if (choice.classList.contains('correct')) {
                        correctAnswer = choiceText;
                    }
                });
                
                questions.push({
                    question: questionText,
                    correct_answer: correctAnswer,
                    choices: choices
                });
            });
            
            // Get text level and difficulty
            const level = levelSelect ? parseInt(levelSelect.value) : 1;
            const difficulty = difficultySelect ? difficultySelect.value : 'medium';
            
            // Save to JSON file and MongoDB
            fetch('/save-qcm-set', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    questions: questions,
                    text_content: textContent,
                    level: level,
                    difficulty: difficulty
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('تم حفظ مجموعة الأسئلة بنجاح', 'success');
                    
                    // Download JSON file
                    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify({
                        text_content: textContent,
                        level: level,
                        difficulty: difficulty,
                        questions: questions
                    }, null, 2));
                    const downloadAnchorNode = document.createElement('a');
                    downloadAnchorNode.setAttribute("href", dataStr);
                    downloadAnchorNode.setAttribute("download", data.file || "qcms.json");
                    document.body.appendChild(downloadAnchorNode);
                    downloadAnchorNode.click();
                    downloadAnchorNode.remove();
                    
                    window.showAlert('تم حفظ الملف في مجلد Saved_qcms', 'success');
                    
                    window.showAlert('تم حفظ الملف في مجلد Saved_qcms', 'success');
                } else {
                    showAlert('حدث خطأ أثناء حفظ مجموعة الأسئلة: ' + data.message, 'error');
                }
            })
            .catch(error => {
                showAlert('حدث خطأ أثناء حفظ مجموعة الأسئلة: ' + error, 'error');
            });
        });
    }
    
    // Generate more questions
    const generateMoreBtn = document.getElementById('generate-more');
    if (generateMoreBtn) {
        generateMoreBtn.addEventListener('click', function() {
            resultsSection.style.display = 'none';
            window.scrollTo(0, 0);
        });
    }
    
    // Clear form
    const clearFormBtn = document.getElementById('clear-form');
    if (clearFormBtn) {
        clearFormBtn.addEventListener('click', function() {
            if (form) form.reset();
            if (resultsSection) resultsSection.style.display = 'none';
            if (ragQuery) ragQuery.value = '';
            if (rawText) rawText.value = '';
            if (paragraphsContainer) paragraphsContainer.style.display = 'none';
            if (paragraphsList) paragraphsList.innerHTML = '';
            selectedParagraphs = [];
        });
    }
    
    // Show file name when selected
    window.showFileName = function(input) {
        const fileNameElement = document.getElementById('file-name');
        const uploadBtn = document.getElementById('upload-btn');
        
        if (input.files && input.files[0]) {
            fileNameElement.textContent = input.files[0].name;
            uploadBtn.style.display = 'inline-block';
        } else {
            fileNameElement.textContent = '';
            uploadBtn.style.display = 'none';
        }
    };
    
    // Handle document upload form submission
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (!fileUpload || !fileUpload.files[0]) {
                showAlert('يرجى اختيار ملف للتحميل', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', fileUpload.files[0]);
            
            if (trainingStatus) {
                trainingStatus.textContent = 'جاري تحميل ملف التدريب...';
                trainingStatus.style.display = 'block';
            }
            
            fetch('/upload-pdf', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('تم تحميل ملف التدريب بنجاح', 'success');
                    if (trainingStatus) trainingStatus.style.display = 'none';
                    
                    // Clear file input
                    if (fileUpload) fileUpload.value = '';
                    if (fileName) fileName.textContent = '';
                    const uploadBtn = document.getElementById('upload-btn');
                    if (uploadBtn) uploadBtn.style.display = 'none';
                } else {
                    showAlert('حدث خطأ أثناء تحميل ملف التدريب: ' + data.message, 'error');
                    if (trainingStatus) trainingStatus.style.display = 'none';
                }
            })
            .catch(error => {
                showAlert('حدث خطأ أثناء تحميل ملف التدريب: ' + error, 'error');
                if (trainingStatus) trainingStatus.style.display = 'none';
            });
        });
    }
    
    // Handle raw text input for paragraph extraction
    if (rawText) {
        rawText.addEventListener('input', function() {
            if (rawText.value.trim().length > 0) {
                // Extract paragraphs
                fetch('/extract-paragraphs', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text: rawText.value
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.paragraphs.length > 0) {
                        displayParagraphs(data.paragraphs);
                        if (paragraphsContainer) paragraphsContainer.style.display = 'block';
                    } else {
                        if (paragraphsContainer) paragraphsContainer.style.display = 'none';
                    }
                })
                .catch(error => {
                    console.error('Error extracting paragraphs:', error);
                    if (paragraphsContainer) paragraphsContainer.style.display = 'none';
                });
            } else {
                if (paragraphsContainer) paragraphsContainer.style.display = 'none';
            }
        });
    }
    
    // Display paragraphs for selection
    function displayParagraphs(paragraphs) {
        if (!paragraphsList) return;
        
        paragraphsList.innerHTML = '';
        selectedParagraphs = [];
        
        // Add select all option
        const selectAllItem = document.createElement('div');
        selectAllItem.className = 'paragraph-item select-all';
        selectAllItem.textContent = 'تحديد/إلغاء تحديد الكل';
        
        selectAllItem.addEventListener('click', function() {
            const allSelected = paragraphsList.querySelectorAll('.paragraph-item:not(.select-all)').length === 
                               paragraphsList.querySelectorAll('.paragraph-item.selected:not(.select-all)').length;
            
            // Toggle selection for all paragraphs
            paragraphsList.querySelectorAll('.paragraph-item:not(.select-all)').forEach((item, idx) => {
                if (allSelected) {
                    // Deselect all
                    item.classList.remove('selected');
                    const index = selectedParagraphs.indexOf(idx);
                    if (index !== -1) {
                        selectedParagraphs.splice(index, 1);
                    }
                } else {
                    // Select all
                    item.classList.add('selected');
                    if (!selectedParagraphs.includes(idx)) {
                        selectedParagraphs.push(idx);
                    }
                }
            });
            
            // Toggle select all button appearance
            selectAllItem.classList.toggle('selected', !allSelected);
        });
        
        paragraphsList.appendChild(selectAllItem);
        
        paragraphs.forEach((paragraph, index) => {
            const paragraphItem = document.createElement('div');
            paragraphItem.className = 'paragraph-item';
            paragraphItem.dataset.index = index;
            paragraphItem.textContent = paragraph;
            
            paragraphItem.addEventListener('click', function() {
                paragraphItem.classList.toggle('selected');
                
                const paragraphIndex = parseInt(paragraphItem.dataset.index);
                
                if (paragraphItem.classList.contains('selected')) {
                    // Add to selected paragraphs
                    if (!selectedParagraphs.includes(paragraphIndex)) {
                        selectedParagraphs.push(paragraphIndex);
                    }
                } else {
                    // Remove from selected paragraphs
                    const idx = selectedParagraphs.indexOf(paragraphIndex);
                    if (idx !== -1) {
                        selectedParagraphs.splice(idx, 1);
                    }
                }
                
                // Update select all button appearance
                const allSelected = paragraphsList.querySelectorAll('.paragraph-item:not(.select-all)').length === 
                                   paragraphsList.querySelectorAll('.paragraph-item.selected:not(.select-all)').length;
                
                const selectAllItem = paragraphsList.querySelector('.select-all');
                if (selectAllItem) {
                    selectAllItem.classList.toggle('selected', allSelected);
                }
            });
            
            paragraphsList.appendChild(paragraphItem);
        });
    }
});
// Function to improve a question
function improveQuestion(index) {
    const card = document.querySelector(`.question-card[data-index="${index}"]`);
    if (!card) return;
    
    const questionTextEl = card.querySelector('.question-text');
    const questionText = questionTextEl.textContent.substring(questionTextEl.textContent.indexOf('. ') + 2);
    
    const choices = [];
    const choiceElements = card.querySelectorAll('.choice');
    let correctAnswer = '';
    
    choiceElements.forEach(choice => {
        const choiceText = choice.querySelector('span[contenteditable="true"]').textContent;
        choices.push(choiceText);
        
        if (choice.classList.contains('correct')) {
            correctAnswer = choiceText;
        }
    });
    
    const question = {
        question: questionText,
        correct_answer: correctAnswer,
        choices: choices
    };
    
    // Show loading state
    const originalContent = card.innerHTML;
    card.innerHTML = '<div class="spinner"></div><p>جاري تحسين السؤال...</p>';
    
    // Send to server for improvement
    fetch('/improve-question', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            text: window.textContent || '',
            question: question
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the question with improved version
            updateQuestionCard(card, data.improved_question, index);
            window.showAlert('تم تحسين السؤال بنجاح', 'success');
        } else {
            // Restore original content
            card.innerHTML = originalContent;
            window.showAlert('حدث خطأ أثناء تحسين السؤال: ' + data.message, 'error');
        }
    })
    .catch(error => {
        // Restore original content
        card.innerHTML = originalContent;
        window.showAlert('حدث خطأ أثناء تحسين السؤال: ' + error, 'error');
    });
}

// Function to update a question card with improved content
function updateQuestionCard(card, improvedQuestion, index) {
    card.innerHTML = '';
    
    const questionText = document.createElement('div');
    questionText.className = 'question-text';
    questionText.contentEditable = true;
    questionText.textContent = `${index + 1}. ${improvedQuestion.question}`;
    
    const choicesList = document.createElement('ul');
    choicesList.className = 'choices';
    
    improvedQuestion.choices.forEach((choice, choiceIndex) => {
        const choiceItem = document.createElement('li');
        choiceItem.className = 'choice';
        if (choice === improvedQuestion.correct_answer) {
            choiceItem.classList.add('correct');
        }
        
        // Create editable choice text
        const choiceText = document.createElement('span');
        choiceText.contentEditable = true;
        choiceText.textContent = choice;
        
        const choiceLabel = document.createElement('span');
        choiceLabel.className = 'choice-label';
        choiceLabel.textContent = `${String.fromCharCode(65 + choiceIndex)}. `;
        
        // Add radio button for selecting correct answer
        const radioBtn = document.createElement('input');
        radioBtn.type = 'radio';
        radioBtn.name = `correct-answer-${index}`;
        radioBtn.className = 'correct-answer-radio';
        radioBtn.checked = choice === improvedQuestion.correct_answer;
        radioBtn.addEventListener('change', function() {
            // Remove correct class from all choices in this question
            choicesList.querySelectorAll('.choice').forEach(c => c.classList.remove('correct'));
            // Add correct class to this choice
            choiceItem.classList.add('correct');
        });
        
        choiceItem.appendChild(radioBtn);
        choiceItem.appendChild(choiceLabel);
        choiceItem.appendChild(choiceText);
        
        choicesList.appendChild(choiceItem);
    });
    
    // Add action buttons
    const actionButtons = document.createElement('div');
    actionButtons.className = 'question-actions';
    
    const saveButton = document.createElement('button');
    saveButton.className = 'action-btn save-btn';
    saveButton.innerHTML = '<i class="fas fa-save"></i>';
    saveButton.title = 'حفظ السؤال';
    saveButton.onclick = function() { saveQuestion(index); };
    
    const deleteButton = document.createElement('button');
    deleteButton.className = 'action-btn delete-btn';
    deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
    deleteButton.title = 'حذف السؤال';
    deleteButton.onclick = function() { deleteQuestion(index); };
    
    const improveButton = document.createElement('button');
    improveButton.className = 'action-btn improve-btn';
    improveButton.innerHTML = '<i class="fas fa-magic"></i>';
    improveButton.title = 'تحسين السؤال';
    improveButton.onclick = function() { improveQuestion(index); };
    
    actionButtons.appendChild(saveButton);
    actionButtons.appendChild(deleteButton);
    actionButtons.appendChild(improveButton);
    
    card.appendChild(questionText);
    card.appendChild(choicesList);
    card.appendChild(actionButtons);
}
// Function to suggest improvements for a question
function suggestImprovements(index) {
    const card = document.querySelector(`.question-card[data-index="${index}"]`);
    if (!card) return;
    
    const questionTextEl = card.querySelector('.question-text');
    const questionText = questionTextEl.textContent.substring(questionTextEl.textContent.indexOf('. ') + 2);
    
    const choices = [];
    const choiceElements = card.querySelectorAll('.choice');
    let correctAnswer = '';
    
    choiceElements.forEach(choice => {
        const choiceText = choice.querySelector('span[contenteditable="true"]').textContent;
        choices.push(choiceText);
        
        if (choice.classList.contains('correct')) {
            correctAnswer = choiceText;
        }
    });
    
    const question = {
        question: questionText,
        correct_answer: correctAnswer,
        choices: choices
    };
    
    // Show loading state
    const originalContent = card.innerHTML;
    card.innerHTML = '<div class="spinner"></div><p>جاري إنشاء اقتراحات التحسين...</p>';
    
    // Send to server for improvement suggestions
    fetch('/suggest-improvements', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            text: window.textContent || '',
            question: question
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show improvement suggestions
            displayImprovementSuggestions(card, data.improvement_suggestion, index);
            window.showAlert('تم إنشاء اقتراحات التحسين بنجاح', 'success');
        } else {
            // Restore original content
            card.innerHTML = originalContent;
            window.showAlert('حدث خطأ أثناء إنشاء اقتراحات التحسين: ' + data.message, 'error');
        }
    })
    .catch(error => {
        // Restore original content
        card.innerHTML = originalContent;
        window.showAlert('حدث خطأ أثناء إنشاء اقتراحات التحسين: ' + error, 'error');
    });
}

// Function to display improvement suggestions
function displayImprovementSuggestions(card, suggestion, index) {
    card.innerHTML = '';
    
    // Create comparison table
    const comparisonTable = document.createElement('div');
    comparisonTable.className = 'comparison-table';
    
    // Add question comparison
    const questionComparison = document.createElement('div');
    questionComparison.className = 'comparison-row';
    
    const originalQuestionLabel = document.createElement('div');
    originalQuestionLabel.className = 'comparison-label';
    originalQuestionLabel.textContent = 'السؤال الأصلي:';
    
    const originalQuestionValue = document.createElement('div');
    originalQuestionValue.className = 'comparison-value original';
    originalQuestionValue.textContent = suggestion.original_question;
    
    const suggestedQuestionLabel = document.createElement('div');
    suggestedQuestionLabel.className = 'comparison-label';
    suggestedQuestionLabel.textContent = 'السؤال المقترح:';
    
    const suggestedQuestionValue = document.createElement('div');
    suggestedQuestionValue.className = 'comparison-value suggested';
    suggestedQuestionValue.textContent = suggestion.suggested_question;
    
    questionComparison.appendChild(originalQuestionLabel);
    questionComparison.appendChild(originalQuestionValue);
    questionComparison.appendChild(suggestedQuestionLabel);
    questionComparison.appendChild(suggestedQuestionValue);
    
    // Add correct answer comparison
    const correctAnswerComparison = document.createElement('div');
    correctAnswerComparison.className = 'comparison-row';
    
    const originalAnswerLabel = document.createElement('div');
    originalAnswerLabel.className = 'comparison-label';
    originalAnswerLabel.textContent = 'الإجابة الصحيحة الأصلية:';
    
    const originalAnswerValue = document.createElement('div');
    originalAnswerValue.className = 'comparison-value original';
    originalAnswerValue.textContent = suggestion.original_correct_answer;
    
    const suggestedAnswerLabel = document.createElement('div');
    suggestedAnswerLabel.className = 'comparison-label';
    suggestedAnswerLabel.textContent = 'الإجابة الصحيحة المقترحة:';
    
    const suggestedAnswerValue = document.createElement('div');
    suggestedAnswerValue.className = 'comparison-value suggested';
    suggestedAnswerValue.textContent = suggestion.suggested_correct_answer;
    
    correctAnswerComparison.appendChild(originalAnswerLabel);
    correctAnswerComparison.appendChild(originalAnswerValue);
    correctAnswerComparison.appendChild(suggestedAnswerLabel);
    correctAnswerComparison.appendChild(suggestedAnswerValue);
    
    // Add choices comparison
    const choicesComparison = document.createElement('div');
    choicesComparison.className = 'comparison-row';
    
    const originalChoicesLabel = document.createElement('div');
    originalChoicesLabel.className = 'comparison-label';
    originalChoicesLabel.textContent = 'الخيارات الأصلية:';
    
    const originalChoicesList = document.createElement('ul');
    originalChoicesList.className = 'comparison-choices original';
    suggestion.original_choices.forEach(choice => {
        const li = document.createElement('li');
        li.textContent = choice;
        if (choice === suggestion.original_correct_answer) {
            li.classList.add('correct');
        }
        originalChoicesList.appendChild(li);
    });
    
    const suggestedChoicesLabel = document.createElement('div');
    suggestedChoicesLabel.className = 'comparison-label';
    suggestedChoicesLabel.textContent = 'الخيارات المقترحة:';
    
    const suggestedChoicesList = document.createElement('ul');
    suggestedChoicesList.className = 'comparison-choices suggested';
    suggestion.suggested_choices.forEach(choice => {
        const li = document.createElement('li');
        li.textContent = choice;
        if (choice === suggestion.suggested_correct_answer) {
            li.classList.add('correct');
        }
        suggestedChoicesList.appendChild(li);
    });
    
    choicesComparison.appendChild(originalChoicesLabel);
    choicesComparison.appendChild(originalChoicesList);
    choicesComparison.appendChild(suggestedChoicesLabel);
    choicesComparison.appendChild(suggestedChoicesList);
    
    // Add improvement notes
    const notesSection = document.createElement('div');
    notesSection.className = 'improvement-notes';
    
    const notesLabel = document.createElement('div');
    notesLabel.className = 'notes-label';
    notesLabel.textContent = 'ملاحظات التحسين:';
    
    const notesValue = document.createElement('div');
    notesValue.className = 'notes-value';
    notesValue.textContent = suggestion.improvement_notes;
    
    notesSection.appendChild(notesLabel);
    notesSection.appendChild(notesValue);
    
    // Add action buttons
    const actionButtons = document.createElement('div');
    actionButtons.className = 'question-actions';
    
    const applyButton = document.createElement('button');
    applyButton.className = 'action-btn apply-btn';
    applyButton.innerHTML = '<i class="fas fa-check"></i>';
    applyButton.title = 'تطبيق التحسينات';
    applyButton.onclick = function() { 
        applyImprovements(index, suggestion.suggested_question, suggestion.suggested_correct_answer, suggestion.suggested_choices); 
    };
    
    const cancelButton = document.createElement('button');
    cancelButton.className = 'action-btn cancel-btn';
    cancelButton.innerHTML = '<i class="fas fa-times"></i>';
    cancelButton.title = 'إلغاء التحسينات';
    cancelButton.onclick = function() { 
        cancelImprovements(index, suggestion.original_question, suggestion.original_correct_answer, suggestion.original_choices); 
    };
    
    actionButtons.appendChild(applyButton);
    actionButtons.appendChild(cancelButton);
    
    // Assemble the card
    comparisonTable.appendChild(questionComparison);
    comparisonTable.appendChild(correctAnswerComparison);
    comparisonTable.appendChild(choicesComparison);
    
    card.appendChild(comparisonTable);
    card.appendChild(notesSection);
    card.appendChild(actionButtons);
}

// Function to apply suggested improvements
function applyImprovements(index, suggestedQuestion, suggestedCorrectAnswer, suggestedChoices) {
    const card = document.querySelector(`.question-card[data-index="${index}"]`);
    if (!card) return;
    
    // Create a new question card with the suggested improvements
    updateQuestionCard(card, {
        question: suggestedQuestion,
        correct_answer: suggestedCorrectAnswer,
        choices: suggestedChoices
    }, index);
    
    window.showAlert('تم تطبيق التحسينات بنجاح', 'success');
}

// Function to cancel suggested improvements
function cancelImprovements(index, originalQuestion, originalCorrectAnswer, originalChoices) {
    const card = document.querySelector(`.question-card[data-index="${index}"]`);
    if (!card) return;
    
    // Restore the original question card
    updateQuestionCard(card, {
        question: originalQuestion,
        correct_answer: originalCorrectAnswer,
        choices: originalChoices
    }, index);
    
    window.showAlert('تم إلغاء التحسينات', 'info');
}
// Function to improve a question
function improveQuestion(index) {
    const card = document.querySelector(`.question-card[data-index="${index}"]`);
    if (!card) return;
    
    const questionTextEl = card.querySelector('.question-text');
    const questionText = questionTextEl.textContent.substring(questionTextEl.textContent.indexOf('. ') + 2);
    
    const choices = [];
    const choiceElements = card.querySelectorAll('.choice');
    let correctAnswer = '';
    
    choiceElements.forEach(choice => {
        const choiceText = choice.querySelector('span[contenteditable="true"]').textContent;
        choices.push(choiceText);
        
        if (choice.classList.contains('correct')) {
            correctAnswer = choiceText;
        }
    });
    
    const question = {
        question: questionText,
        correct_answer: correctAnswer,
        choices: choices
    };
    
    // Show loading state
    const originalContent = card.innerHTML;
    card.innerHTML = '<div class="spinner"></div><p>جاري تحسين السؤال...</p>';
    
    // Send to server for improvement
    fetch('/improve-question', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            text: window.textContent || '',
            question: question
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the question with improved version
            updateQuestionCard(card, data.improved_question, index);
            window.showAlert('تم تحسين السؤال بنجاح', 'success');
        } else {
            // Restore original content
            card.innerHTML = originalContent;
            window.showAlert('حدث خطأ أثناء تحسين السؤال: ' + data.message, 'error');
        }
    })
    .catch(error => {
        // Restore original content
        card.innerHTML = originalContent;
        window.showAlert('حدث خطأ أثناء تحسين السؤال: ' + error, 'error');
    });
}