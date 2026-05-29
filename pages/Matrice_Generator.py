import streamlit as st
import numpy as np
import random
import pandas as pd

# إعدادات الصفحة
st.set_page_config(page_title="Générateur de Matrice d'Incompatibilité", layout="wide")

st.title("📊 Générateur Optimisé de Matrice d'Incompatibilité & Stérilisation")
st.write("قم بتحديد المدخلات من الشريط الجانبي ثم اضغط على الأزرار لتوليد المصفوفات المطلوبة.")

# تهيئة الـ session_state للاحتفاظ بالبيانات عند الانتقال بين الأزرار
if 'Incomp' not in st.session_state:
    st.session_state.Incomp = None
if 'N' not in st.session_state:
    st.session_state.N = 0
if 'categories' not in st.session_state:
    st.session_state.categories = None
if 'taux_voulu' not in st.session_state:
    st.session_state.taux_voulu = 0.0
if 'taux_final' not in st.session_state:
    st.session_state.taux_final = 0.0
if 'nb_final' not in st.session_state:
    st.session_state.nb_final = 0
if 'total_pairs' not in st.session_state:
    st.session_state.total_pairs = 0
# إضافة متغير للاحتفاظ بمصفوفة التعقيم المستوردة أو المولدة لتسهيل التعامل مع الملفات الخارجة
if 'Ts_matrix' not in st.session_state:
    st.session_state.Ts_matrix = None

# =========================================================
# وظائف الحساب الأساسية
# =========================================================

def calculer_incomp_matrix(categories):
    N = len(categories)
    cat_row = categories.reshape(1, N)
    cat_col = categories.reshape(N, 1)
    Incomp = (cat_row != cat_col).astype(int)
    np.fill_diagonal(Incomp, 0)
    return Incomp

def calculer_nb_incompatibilites(categories):
    Incomp = calculer_incomp_matrix(categories)
    return np.sum(Incomp)

def generer_matrice_sterilisation(Incomp):
    N = Incomp.shape[0]
    Ts = np.zeros((N, N), dtype=int)
    
    for i in range(N):
        for j in range(i + 1, N):
            if Incomp[i, j] == 1:
                # توليد قيمة عشوائية متناظرة بين 1 و 99 لـ Ts(i,j) و Ts(j,i)
                valeur_aleatoire = random.randint(1, 99)
                Ts[i, j] = valeur_aleatoire
                Ts[j, i] = valeur_aleatoire
            else:
                # القيمة 10 ثابتة عند التوافق
                Ts[i, j] = 10
                Ts[j, i] = 10
                
    # تأكيد أن القطر الرئيسي صفر تماماً Ts(i,i) = 0
    np.fill_diagonal(Ts, 0)
    return Ts

# =========================================================
# محرك البحث والتحسين
# =========================================================
def optimiser_repartition(N, taux_cible, max_classes):
    total_pairs = N * (N - 1)
    nb_cible = round((taux_cible / 100) * total_pairs)
    
    # ✅ الحل: نبدأ بجعل كل المنتجات في الفئة 1 (نسبة عدم توافق = 0%)
    # هذا يمنح الخوارزمية حرية كاملة للصعود تدريجياً وبدقة نحو النسبة المطلوبة
    categories = np.ones(N, dtype=int)
    
    best_categories = categories.copy()
    min_diff = abs(calculer_nb_incompatibilites(categories) - nb_cible)

    for i in range(100000):
        current_nb = calculer_nb_incompatibilites(categories)
        if current_nb == nb_cible:
            break

        idx = random.randint(0, N - 1)
        old_val = categories[idx]
        new_val = random.randint(1, max_classes) 
        
        categories[idx] = new_val
        new_diff = abs(calculer_nb_incompatibilites(categories) - nb_cible)

        # قبول التغيير إذا كان يقربنا من الهدف أو إذا كان مساوياً له
        if new_diff <= min_diff:
            min_diff = new_diff
            best_categories = categories.copy()
        else:
            # إعطاء فرصة صغيرة (1%) للقبول العشوائي للخروج من الحواجز الرياضية
            if random.random() > 0.01: 
                categories[idx] = old_val

    res = best_categories.copy()
    unique_classes = sorted(np.unique(res))
    mapping = {old: new for new, old in enumerate(unique_classes, 1)}
    for old_id, new_id in mapping.items():
        res[best_categories == old_id] = new_id
        
    return res

# =========================================================
# واجهة المستخدم (Streamlit UI)
# =========================================================

st.sidebar.header("⚙️ معطيات الإدخال")

input_N = st.sidebar.number_input(
    "Nombre total de produits (N) :", 
    min_value=1, 
    max_value=200, 
    value=20, 
    step=1
)

input_taux_voulu = st.sidebar.slider(
    "Taux d'incompatibilité voulu (%) :", 
    min_value=0.0, 
    max_value=100.0, 
    value=30.0, 
    step=0.5
)

# إضافة متحكم في الشريط الجانبي لتحديد أقصى عدد فئات مسموح
max_classes = st.sidebar.number_input(
    "Max Classes :",
    min_value=2,
    max_value=20,
    value=6
)


# أزرار التوليد في الشريط الجانبي
bttn_incomp = st.sidebar.button("Generate Matrice Incompatibilité", use_container_width=True)
bttn_temp = st.sidebar.button("Generate Matrice Temp Sterlisation", use_container_width=True)

# ---------------------------------------------------------
# الحدث الأول: الضغط على زر توليد مصفوفة عدم التوافق
# ---------------------------------------------------------
if bttn_incomp:
    with st.spinner("جاري تشغيل خوارزمية التحسين..."):
        st.session_state.N = input_N
        st.session_state.taux_voulu = input_taux_voulu
        st.session_state.categories = optimiser_repartition(input_N, input_taux_voulu, max_classes)
        st.session_state.Incomp = calculer_incomp_matrix(st.session_state.categories)
        st.session_state.nb_final = np.sum(st.session_state.Incomp)
        st.session_state.total_pairs = input_N * (input_N - 1)
        st.session_state.taux_final = (st.session_state.nb_final / st.session_state.total_pairs) * 100

# عرض نتائج مصفوفة عدم التوافق إذا كانت متوفرة في الذاكرة
if st.session_state.Incomp is not None:
    st.markdown("---")
    st.subheader("📊 نتائج مصفوفة عدم التوافق (Matrice d'incompatibilité)")
    
    # ➕ إضافة خيار استيراد مصفوفة عدم التوافق من ملف txt بجانب مصفوفة الاستيراد
    file_incomp = st.file_uploader("📥 Importer Matrice Incompatibilité (.txt)", type=["txt"], key="upload_incomp")
    if file_incomp is not None:
        try:
            loaded_matrix = np.loadtxt(file_incomp, dtype=int)
            if loaded_matrix.ndim == 2 and loaded_matrix.shape[0] == loaded_matrix.shape[1]:
                st.session_state.Incomp = loaded_matrix
                st.session_state.N = loaded_matrix.shape[0]
                st.session_state.nb_final = np.sum(st.session_state.Incomp)
                st.session_state.total_pairs = st.session_state.N * (st.session_state.N - 1)
                st.session_state.taux_final = (st.session_state.nb_final / st.session_state.total_pairs) * 100
                
                # ✨ الكود المضاف: تحليل واستنتاج الفئات بناءً على البيانات المستوردة من الملف النصي
                comp_matrix = (loaded_matrix == 0).astype(int)
                visited = np.zeros(st.session_state.N, dtype=bool)
                extracted_categories = np.zeros(st.session_state.N, dtype=int)
                current_class = 1
                
                for i in range(st.session_state.N):
                    if not visited[i]:
                        # البحث عن جميع العناصر المتوافقة (0 في المصفوفة الأصلية) لتشكل فئة واحدة
                        queue = [i]
                        visited[i] = True
                        while queue:
                            curr = queue.pop(0)
                            extracted_categories[curr] = current_class
                            for neighbor in range(st.session_state.N):
                                if comp_matrix[curr, neighbor] == 1 and not visited[neighbor]:
                                    visited[neighbor] = True
                                    queue.append(neighbor)
                        current_class += 1
                
                st.session_state.categories = extracted_categories
            else:
                st.error("⚠️ الملف النصي لا يحتوي على مصفوفة مربعة صحيحة.")
        except Exception as e:
            st.error(f"❌ خطأ أثناء قراءة الملف: {e}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="التناسب المطلوب", value=f"{st.session_state.taux_voulu:.2f} %")
    with col2:
        st.metric(label="التناسب المحقق", value=f"{st.session_state.taux_final:.2f} %", delta=f"{st.session_state.taux_final - st.session_state.taux_voulu:.2f} %")
    with col3:
        st.metric(label="عدد حالات عدم التوافق", value=f"{int(st.session_state.nb_final)} / {st.session_state.total_pairs}")

    # عرض جدول مصفوفة عدم التوافق
    df_incomp = pd.DataFrame(
        st.session_state.Incomp, 
        index=[f"P{i+1}" for i in range(st.session_state.N)], 
        columns=[f"P{j+1}" for j in range(st.session_state.N)]
    )
    st.dataframe(df_incomp, use_container_width=True)

    # تفاصيل الفئات
    st.subheader("🗂️ توزيع المنتجات على الفئات (Répartition)")
    classes, counts = np.unique(st.session_state.categories, return_counts=True)
    col_left, col_right = st.columns([1, 2])
    with col_left:
        for cl, ct in zip(classes, counts):
            st.info(f"🔹 **Classe {int(cl)}** : {ct} produits")
    with col_right:
        df_cat = pd.DataFrame({
            "Produit": [f"P{i+1}" for i in range(st.session_state.N)],
            "Classe Affectée": st.session_state.categories
        })
        st.dataframe(df_cat.T, use_container_width=True)

# ---------------------------------------------------------
# الحدث الثاني: الضغط على زر توليد مصفوفة أزمنة التعقيم
# ---------------------------------------------------------
if bttn_temp:
    if st.session_state.Incomp is None:
        st.error("⚠️ يرجى توليد مصفوفة عدم التوافق أولاً بالضغط على الزر الأول!")
    else:
        st.session_state.markdown_visible = True
        with st.spinner("جاري بناء مصفوفة أزمنة التعقيم المتناظرة..."):
            st.session_state.Ts_matrix = generer_matrice_sterilisation(st.session_state.Incomp)

# التحقق من وجود مصفوفة أزمنة التعقيم لعرضها وإضافة خيار الاستيراد بجانبها
if st.session_state.Ts_matrix is not None or bttn_temp:
    if st.session_state.Incomp is not None:
        st.markdown("---")
        st.subheader("⏱️ مصفوفة أزمنة التعقيم المحسوبة (Temp_Sterlisation - Ts)")
        st.info("💡 تم حساب هذه مصفوفة كمرآة متناظرة: قيمة 10 عند التوافق (0)، وقيمة عشوائية [1-99] عند عدم التوافق (1)، والقطر صفري.")
        
        # ➕ إضافة خيار استيراد مصفوفة أزمنة التعقيم من ملف txt بجانب الجدول
        file_ts = st.file_uploader("📥 Importer Matrice Temp Stérilisation (.txt)", type=["txt"], key="upload_ts")
        if file_ts is not None:
            try:
                loaded_ts = np.loadtxt(file_ts, dtype=int)
                if loaded_ts.ndim == 2 and loaded_ts.shape[0] == st.session_state.N:
                    st.session_state.Ts_matrix = loaded_ts
                else:
                    st.error(f"⚠️ يجب أن تكون أبعاد المصفوفة المستوردة مطابقة لعدد المنتجات الحالي ({st.session_state.N}x{st.session_state.N}).")
            except Exception as e:
                st.error(f"❌ خطأ أثناء قراءة الملف: {e}")

        if st.session_state.Ts_matrix is not None:
            # تحويلها إلى DataFrame للعرض التفاعلي المنظم
            df_ts = pd.DataFrame(
                st.session_state.Ts_matrix,
                index=[f"P{i+1}" for i in range(st.session_state.N)],
                columns=[f"P{j+1}" for j in range(st.session_state.N)]
            )
            st.dataframe(df_ts, use_container_width=True)
