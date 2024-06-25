import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
import sqlite3
from PIL import Image
import pandas as pd
import numpy as np
import re
import io



def img_to_txt(path):
    input_img = Image.open(path)

    #converting image to array format
    image_arr= np.array(input_img)

    reader = easyocr.Reader(['en'])
    text = reader.readtext(image_arr, detail=0)

    return text, input_img



def extract_text(texts):
    extract_dict = {"NAME":[],
                    "DESIGNATION":[],
                    "COMPANY NAME": [],
                    "CONTACT":[],
                    "EMAIL":[],
                    "WEBSITE":[],
                    "ADDRESS":[],
                    "PINCODE":[]}
    

    extract_dict["NAME"].append(texts[0])
    extract_dict["DESIGNATION"].append(texts[1])
    
    for i in range(2, len(texts)):
        if texts[i].startswith("+") or (texts[i].replace("-","").isdigit() and "-" in texts[i]):
            extract_dict["CONTACT"].append(texts[i])

        elif "@" in texts[i] and ".com" in texts[i]:
            extract_dict["EMAIL"].append(texts[i])

        elif "WWW" in texts[i] or "www" in texts[i]:
            small = texts[i].lower()
            extract_dict["WEBSITE"].append(small)

        elif "Tamil Nadu" in texts[i] or "TamilNadu" in  texts[i] or texts[i].isdigit():
            extract_dict["PINCODE"].append(texts[i])

        elif re.match(r'^[A-Za-z]',  texts[i]):
            extract_dict["COMPANY NAME"].append( texts[i])

        else:
            remove_colon = re.sub(r'[,;]', '', texts[i])
            extract_dict["ADDRESS"].append(remove_colon)

    for key,value in extract_dict.items():
        if len(value)>0:
            concadenate = " ".join(value)
            extract_dict[key] = [concadenate]
        
        else:
            value = "NA"
            extract_dict[key] = [value]

    return extract_dict





########################################################## STREAMLIT PART ###################################################################

st.set_page_config(layout="wide")
st.title("BIZCARDX BUSINESS CARD DATA WITH OCR")

with st.sidebar:
    select = option_menu("MAIN MENU", ["HOME", "UPLOAD & MODIFYING", "DELETE"])

if select == "HOME":
    pass

elif select == "UPLOAD & MODIFYING":
    img = st.file_uploader("Upload the Image", type=["png", "jpg", "jpeg"])

    if img is not None:
        st.image(img, width=400)
        text_image, input_image = img_to_txt(img)
        text_dict = extract_text(text_image)

        if text_dict:
            st.success("TEXT IS EXTRACTED SUCCESSFULLY")

        df = pd.DataFrame(text_dict)

        # converting image to bytes

        Image_bytes= io.BytesIO()
        input_image.save(Image_bytes, format= "PNG")    

        Image_data = Image_bytes.getvalue()

        # creating dictionary

        data = {"IMAGE":[Image_data]}

        df1 = pd.DataFrame(data)

        concadenate_df = pd.concat([df,df1],axis=1)
        st.dataframe(concadenate_df)

        button_1 = st.button("save")
        if button_1:
            mydb = sqlite3.connect("bizcardx.db")

            cursor = mydb.cursor()

            create_query = '''CREATE TABLE IF NOT EXISTS bizcard_details(name VARCHAR(255),
                                                                    designation VARCHAR(255),
                                                                    company_name VARCHAR(255),
                                                                    contact VARCHAR(255),
                                                                    email VARCHAR(255),
                                                                    website TEXT,
                                                                    address TEXT,
                                                                    pincode VARCHAR(255),
                                                                    image LONGBLOB)'''

            cursor.execute(create_query)
            mydb.commit()

            insert_query = '''INSERT INTO bizcard_details(name, designation,
                                                         company_name,contact,
                                                         email, website, address,
                                                         pincode, image)

                                                         values(?,?,?,?,?,?,?,?,?)'''

            datas = concadenate_df.values.tolist()[0]
            cursor.execute(insert_query,datas)
            mydb.commit()

            st.success("SUCCESSFULLY SAVED")
        
            method= st.radio("select the method",["None","Preview","Modify"])

            if method == "None":
                st.write("")

            if method == "Preview":
                mydb = sqlite3.connect("bizcardx.db")
                cursor = mydb.cursor()

                select_query = "select * from bizcard_details"
                cursor.execute(select_query)
                table = cursor.fetchall()
                mydb.commit()

                table_df = pd.DataFrame(table,columns = ("NAME","DESIGNATION","COMPANY NAME", "CONTACT","EMAIL", "WEBSITE", "ADDRESS","PINCODE", "IMAGE"))
                
                st.dataframe(table_df)

            elif method == "Modify":
                mydb = sqlite3.connect("bizcardx.db")
                cursor = mydb.cursor()

                select_query = "select * from bizcard_details"
                cursor.execute(select_query)
                table = cursor.fetchall()
                mydb.commit()

                table_df = pd.DataFrame(table,columns = ("NAME","DESIGNATION","COMPANY NAME", "CONTACT","EMAIL", "WEBSITE", "ADDRESS","PINCODE", "IMAGE"))   

                col1,col2 = st.columns(2)
                with col1:
                    select_name = st.selectbox("SELECT THE NAME", table_df["NAME"])

                df2= table_df[table_df["NAME"] == select_name]

                df3 = df2.copy()

                col1,col2 = st.columns(2)
                with col1:
                    modify_name = st.text_input("NAME", df2["NAME"].unique()[0]) 
                    modify_design = st.text_input("DESIGNATION", df2["DESIGNATION"].unique()[0]) 
                    modify_comp_name = st.text_input("COMPANY NAME", df2["COMPANY NAME"].unique()[0]) 
                    modify_contact = st.text_input("CONTACT", df2["CONTACT"].unique()[0]) 
                    modify_email = st.text_input("EMAIL", df2["EMAIL"].unique()[0]) 

                    df3["NAME"] = modify_name
                    df3["DESIGNATION"] = modify_design
                    df3["COMPANY NAME"] = modify_comp_name
                    df3["CONTACT"] = modify_contact
                    df3["EMAIL"] = modify_email

                with col2:
                    modify_website = st.text_input("WEBSITE", df2["WEBSITE"].unique()[0]) 
                    modify_address = st.text_input("ADDRESS", df2["ADDRESS"].unique()[0]) 
                    modify_pincode = st.text_input("PINCODE", df2["PINCODE"].unique()[0]) 
                    modify_image = st.text_input("IMAGE", df2["IMAGE"].unique()[0]) 

                    df3["WEBSITE"] = modify_website
                    df3["ADDRESS"] = modify_address
                    df3["PINCODE"] = modify_pincode
                    df3["IMAGE"] = modify_image
                
                st.dataframe(df3)

                col1,col2 = st.columns(2)
                with col1:
                    button_2 = st.button("Modify", use_container_width=True)

                if button_2:
                    mydb = sqlite3.connect("bizcardx.db")
                    cursor = mydb.cursor()

                    cursor.execute(f"DELETE FROM bizcard_details WHERE NAME = '{select_name}'")
                    mydb.commit()



                    insert_query = '''INSERT INTO bizcard_details(name, designation,
                                                                    company_name,contact,
                                                                    email, website, address,
                                                                    pincode, image)

                                                                    values(?,?,?,?,?,?,?,?,?)'''

                    datas = df3.values.tolist()[0]
                    cursor.execute(insert_query,datas)
                    mydb.commit()

                    st.success("SUCCESSFULLY MODIFIED")



elif select == "DELETE":
    mydb = sqlite3.connect("bizcardx.db")
    cursor = mydb.cursor()

    col1,col2 = st.columns(2)
    with col1:
        select_query = "select NAME from bizcard_details"
        cursor.execute(select_query)
        table1 = cursor.fetchall()
        mydb.commit()
        names = []

        for i in table1:
            names.append(i[0])

        name_select = st.selectbox("SELECT THE NAME",names)

    with col2:
        select_query = f"select DESIGNATION from bizcard_details WHERE NAME = '{name_select}'"
        cursor.execute(select_query)
        table2 = cursor.fetchall()
        mydb.commit()
        designation = []

        for j in table2:
            designation.append(j[0])

        design_select = st.selectbox("SELECT THE DESIGNATION",designation)

    if name_select and design_select:
        col1,col2,col3 = st.columns(3)

        with col1:
            st.write(f"SELECT NAME : {name_select}")
            st.write("")
            st.write("")
            st.write("")
            st.write(f"SELECT DESIGNATION : {design_select}")

        with col2:
            st.write("")
            st.write("")
            st.write("")

            remove = st.button("Delete")

            if remove:
                cursor.execute(f"DELETE FROM bizcard_details WHERE NAME= '{name_select}' AND DESIGNATION= '{design_select}'")
                mydb.commit()

                st.warning("DELETED")
