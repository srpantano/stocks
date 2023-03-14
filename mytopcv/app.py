import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from PIL import Image
#from ai_improver import * 
from constants import * 
#from cv_scanner import *
from io import StringIO
import openai

class App():

    def __generalCorrector(self, prompt, temperature, model=OPENAIMODEL, maxTokens = 20):
        openai.api_key = OPENAIKEY
        res = openai.Completion.create(model=model, prompt=prompt, temperature=temperature, max_tokens=maxTokens)
        return res['choices'][0]['text']


    def start(self) -> None:

        st.markdown('<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-GLhlTQ8iRABdZLl6O3oVMWSktQOp6b7In1Zl3/Jr59b6EGGoI1aFkw7cmDA6j6gD" crossorigin="anonymous">',
                    unsafe_allow_html=True)

        st.markdown("""
            <nav class="navbar fixed-top navbar-expand-lg navbar-light" style="background-color: #59B4E3;">
                <a class="navbar-brand" href="#">Molecular Data</a>
                <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav">
                    <li class="nav-item active">
                        <a class="nav-link" href="#">Home <span class="sr-only">(current)</span></a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#">Features</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#">Pricing</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link disabled" href="#">Disabled</a>
                    </li>
                    </ul>
                </div>         
            </nav>   
        """, unsafe_allow_html=True)

        st.title("Analise seu currículo utilizando a Inteligência Artificial ChatGPT3")    
        image = Image.open('ibmec_br.jpg')
        st.subheader('Esta aplicação tem como objetivo melhorar a qualidade do seu CV usando a nova inteligência artificial ChatGPT3')
        st.image(image, caption='foto de ibmec.br')

    def downloadTemplate(self, templateFile=TEMPLATE_FILE) -> None:
        contentFile = open(templateFile,'r')
        content = contentFile.read()
        st.subheader("Modelo a ser preenchido:")
        st.download_button(label='Template', 
                           data=content,
                           file_name=TEMPLATE_FILE,
                           mime='text/plain', 
                           help="Baixe e preencha o template")
        contentFile.close()

    def uploadCV(self, templateFile=TEMPLATE_FILE) -> None:
        return st.file_uploader(label="Faça o upload do template preenchido aqui:", type='txt') 

    def summaryResult(self, cvData) -> str:

        def getFixedkeyText(key,text) -> str:

            keyOrder = ORDERED_KEYS.index(key)
            nextKey = ORDERED_KEYS[keyOrder+1]
            startText =  text.split(key+':')[1]
            findStop = startText.find(nextKey)
            trimmedText = startText[0:findStop]
            trimmedText = trimmedText.replace('\n','')

            return trimmedText

        trimmedText=getFixedkeyText(FIXED_KEYS[1],cvData)

        firstText = self.__generalCorrector(prompt=SUMMARY_PROMPT_CONVERT+trimmedText, temperature=TEMPERATURE_SUMMARY_PROMPT_CONVERT, maxTokens=200)
        finalText = self.__generalCorrector(prompt=SUMMARY_PROMPT_IMPROVER+firstText, temperature=TEMPERATURE_SUMMARY_PROMPT_IMPROVER, maxTokens=200)
        
        return finalText    

    def __getTextFromDoc(self, document) -> str:
        stringio = StringIO(document.getvalue().decode("utf-8"))
        return stringio.read()

    def __processSummary(self, uploaded_file) -> None:

        st.subheader('Olha o resumo do seu CV...')
        st.write(self.summaryResult(self.__getTextFromDoc(uploaded_file)))

    def __improveExperience(self, experience_text) -> str:

        correct_text = self.__generalCorrector(prompt=EXPERIENCE_PROMPT_CONVERT+experience_text, temperature=0.4, maxTokens=200)
        #st.markdown("<span style='color:navy'>"+experience_text+"</span>", unsafe_allow_html=True)
        #st.write(experience_text)
        #st.text('The AI suggests the following summary instead: \n')
        #print(final_correction)
        #st.markdown("<span style='color:red'>"+correct_text+"</span>", unsafe_allow_html=True)
        #st.write(experience_text)
        return correct_text

    def __processExperience(self, uploaded_file) -> None:
        
        def splitExperiences(cvData) -> list:

            listExperiences = cvData.split(VARIABLE_KEYS[0]+ ' ')
            
            selectedExperience = []

            for l in listExperiences[1:]:                

                try:
                    int(l[0][0])
                    selectedExperience.append(l)
                except:
                    continue

            selectedExperience[-1] = selectedExperience[-1].split(ORDERED_KEYS[5])[0]

            return selectedExperience

        experiences = splitExperiences(self.__getTextFromDoc(uploaded_file))
        reviewedExperiences = []

        for e in experiences:
            
            reviewExperience = self.__improveExperience(e.split('[SEP]')[-2])
            reviewedExperiences.append(reviewExperience)

        for e in range(len(reviewedExperiences)):
            st.write('\nEXPERIÊNCIA %i \n'%(e+1))
            st.write(reviewedExperiences[e])

    def process(self, uploaded_file) -> None:
        self.__processSummary(uploaded_file)
        self.__processExperience(uploaded_file)


if __name__=='__main__':
    app = App()
    app.start()
    app.downloadTemplate()
    uploaded_file = app.uploadCV()
    
    if uploaded_file is not None:
        app.process(uploaded_file)

    