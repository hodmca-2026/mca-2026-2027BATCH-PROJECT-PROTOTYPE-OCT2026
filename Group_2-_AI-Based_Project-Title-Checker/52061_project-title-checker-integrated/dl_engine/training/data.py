"""
Illustrative Academic Project Dataset
=====================================
PROVENANCE AND USAGE NOTE:
This dataset contains 182 curated illustrative project proposals (titles and abstracts)
across 7 domains (26 per domain). These examples were created specifically for initial
development, experimental validation, and educational syllabus demonstration.
They are NOT genuine student submissions and do NOT establish production real-world accuracy.
"""

from typing import List, Tuple

# Each entry is a tuple: (title: str, description: str, domain: str)
ACADEMIC_PROPOSALS: List[Tuple[str, str, str]] = [
    # ========================================================
    # 1. Agriculture (26 examples)
    # ========================================================
    (
        "Smart Irrigation System Using Soil Moisture Sensors and Weather Forecasting",
        "Automates field water distribution based on ground capacitance sensors, ambient humidity, and rainfall predictions to optimize agricultural water consumption.",
        "Agriculture",
    ),
    (
        "Crop Disease Detection and Leaf Health Diagnosis with Deep Learning",
        "Uses convolutional neural networks to identify fungal and viral plant infections from photos of diseased crop leaves and foliage.",
        "Agriculture",
    ),
    (
        "Fertilizer Recommendation System Based on Soil NPK Values and pH",
        "Recommends targeted chemical and organic fertilizer dosages according to measured nitrogen, phosphorus, potassium, and soil acidity levels.",
        "Agriculture",
    ),
    (
        "Automated Plant Leaf Pest Identification Using Drone Aerial Imagery",
        "Detects insect infestations and caterpillar damage in agricultural fields using aerial drone camera imagery and object detection models.",
        "Agriculture",
    ),
    (
        "Greenhouse Climate Control System with IoT Sensors and Microcontrollers",
        "Monitors and controls indoor greenhouse temperature, misting, soil hydration, and ventilation fans for protected horticulture crops.",
        "Agriculture",
    ),
    (
        "Grain Quality Assessment and Sorting Machine Using Computer Vision",
        "Inspects harvested rice, wheat, and pulses on a conveyor belt, categorizing grain purity and detecting foreign debris using optical cameras.",
        "Agriculture",
    ),
    (
        "Farm Produce Supply Chain Traceability Using Blockchain Technology",
        "Tracks agricultural crops from harvest through distribution and retail stores using cryptographic distributed ledger transactions.",
        "Agriculture",
    ),
    (
        "Livestock Health Monitoring and Heat Detection Collar with Accelerometers",
        "Monitors dairy cow rumination cycles, body temperature, and estrus heat cycles using wearable neck collars with wireless telemetry.",
        "Agriculture",
    ),
    (
        "Weed Detection and Targeted Herbicide Spraying Robot for Precision Agriculture",
        "Employs autonomous wheeled robots with computer vision to spot-spray unwanted weed vegetation while preserving growing crops.",
        "Agriculture",
    ),
    (
        "Agricultural Yield Prediction Based on Weather and Soil Nutrients",
        "Estimates seasonal hectare crop yield using historical rainfall, solar radiation, soil fertility indexes, and machine learning regressors.",
        "Agriculture",
    ),
    (
        "Automated Hydroponics Nutrient Dosing and pH Regulation System",
        "Regulates electrical conductivity and water nutrient solution balance in soilless vertical farming using automated peristaltic pumps.",
        "Agriculture",
    ),
    (
        "Rice Blast Disease Severity Classification Using Deep Neural Networks",
        "Analyzes paddy leaf lesions to evaluate blast disease progression and generate timely fungicide intervention schedules.",
        "Agriculture",
    ),
    (
        "Fruit Ripeness and Defect Detection Conveyor System with Spectral Imaging",
        "Classifies harvested apples, oranges, and mangoes into export grades based on color uniformity, firmness, and surface bruises.",
        "Agriculture",
    ),
    (
        "Sugarcane Harvest Maturity Prediction Using Satellite Remote Sensing",
        "Computes vegetation indices from optical satellite bands to forecast optimal harvesting schedules for regional sugarcane mills.",
        "Agriculture",
    ),
    (
        "Soil Salinity and Moisture Mapping for Arid Zone Farming",
        "Combines electromagnetic induction sensors and GPS mapping to identify salt accumulation in irrigated agricultural soils.",
        "Agriculture",
    ),
    (
        "Pest Population Growth Forecasting Using Microclimate Sensor Networks",
        "Forecasts locust and whitefly breeding swarms using thermal accumulation degree-day algorithms and field weather stations.",
        "Agriculture",
    ),
    (
        "Wheat Stripe Rust Early Warning Network Using Distributed Spore Traps",
        "Samples airborne fungal spores in wheat belts and integrates meteorological dispersion simulations to alert local farmers.",
        "Agriculture",
    ),
    (
        "Drone-Based Multispectral Canopy Health and NDVI Indexing",
        "Calculates normalized difference vegetation index maps across farm acreage to guide variable-rate nitrogen application.",
        "Agriculture",
    ),
    (
        "Smart Autonomous Farm Tractor Navigation and Furrow Tracking",
        "Steers agricultural tractors along planned field furrows using RTK-GPS correction and computer vision obstacle detection.",
        "Agriculture",
    ),
    (
        "Solar-Powered Drip Irrigation Controller for Remote Farmland",
        "Powers smart valve timers and soil sensors using photovoltaic battery banks in un-electrified rural agricultural plots.",
        "Agriculture",
    ),
    (
        "Dairy Cattle Milk Yield Estimation Based on Feeding Regimes and Rumination",
        "Predicts daily lactation yields per cow from nutritional feed intake records and wearable activity collar sensors.",
        "Agriculture",
    ),
    (
        "Tea Leaf Disease Identification and Plucking Quality Inspection",
        "Inspects two-leaves-and-a-bud plucking quality and detects blister blight in tea plantations using handheld mobile vision.",
        "Agriculture",
    ),
    (
        "Poultry Farm Ammonia Gas and Environmental Climate Automation",
        "Monitors broiler coop ammonia gas concentrations, air temperature, and litter humidity to prevent avian respiratory distress.",
        "Agriculture",
    ),
    (
        "Aquaculture Shrimp Pond Water Quality and Dissolved Oxygen Controller",
        "Regulates paddlewheel aerators based on real-time optical dissolved oxygen probes and salinity measurements in coastal prawn ponds.",
        "Agriculture",
    ),
    (
        "Cotton Bollworm Damage Detection Using Optical Field Traps",
        "Counts captured nocturnal moth pests in automated solar light traps to determine pest thresholds and bio-pesticide timing.",
        "Agriculture",
    ),
    (
        "Organic Compost Temperature and Aeration Management Telemetry",
        "Tracks microbial decomposition core temperatures in agricultural composting piles to ensure weed seed eradication.",
        "Agriculture",
    ),

    # ========================================================
    # 2. Healthcare (26 examples)
    # ========================================================
    (
        "Skin Cancer Detection Using Convolutional Neural Networks and Dermatoscopy",
        "Classifies dermoscopic skin lesion images into melanoma or benign nevi using deep transfer learning neural network models.",
        "Healthcare",
    ),
    (
        "Heart Disease Risk Prediction System with Clinical Biomarkers",
        "Estimates patient coronary heart disease risk from cholesterol, blood pressure, fasting sugar, and resting ECG parameters.",
        "Healthcare",
    ),
    (
        "Diabetic Retinopathy Classification from Fundus Images Using Deep Learning",
        "Grades macular edema and microaneurysms from digital retinal fundus photography to screen for diabetic eye disease.",
        "Healthcare",
    ),
    (
        "Brain Tumor Segmentation and Volume Estimation Using MRI Scans",
        "Delineates glioblastoma and edema boundaries in multi-modal brain magnetic resonance imaging scans using volumetric U-Net architectures.",
        "Healthcare",
    ),
    (
        "Automated Medical Prescription Verification and Drug Interaction Checker",
        "Analyzes doctor prescription text to alert pharmacists regarding adverse drug-drug interactions, contraindications, and incorrect dosages.",
        "Healthcare",
    ),
    (
        "COVID-19 Chest X-Ray Diagnosis System with Transfer Learning",
        "Screens digital anterior-posterior chest radiographs for viral pneumonia consolidation and ground-glass pulmonary opacities.",
        "Healthcare",
    ),
    (
        "Telemedicine Portal with Patient Vital Signs Remote Monitoring",
        "Connects rural patients with remote physicians, transmitting pulse oximeter readings, digital stethoscope audio, and blood pressure logs.",
        "Healthcare",
    ),
    (
        "Mental Health Chatbot for Anxiety and Depression Assessment",
        "Converses with users using cognitive behavioral therapy prompts to score validated psychometric depression and generalized anxiety indexes.",
        "Healthcare",
    ),
    (
        "Early Detection of Alzheimer Disease from Neuroimaging and Cognitive Tests",
        "Predicts mild cognitive impairment conversion to dementia using structural hippocampal MRI volumetric atrophy and memory score tracking.",
        "Healthcare",
    ),
    (
        "Arrhythmia ECG Waveform Classification Using Deep Residual Networks",
        "Detects premature ventricular contractions, atrial fibrillation, and sinus bradycardia in 12-lead electrocardiogram signals.",
        "Healthcare",
    ),
    (
        "Histopathology Whole Slide Image Analysis for Breast Cancer Grading",
        "Identifies mitotic figures and invasive ductal carcinoma cell clusters in digitized tissue biopsies stained with hematoxylin and eosin.",
        "Healthcare",
    ),
    (
        "Stroke Risk Stratification Model Using Carotid Ultrasound Doppler Signals",
        "Evaluates carotid arterial stenosis, plaque ulceration, and blood velocity profiles to predict transient ischemic attacks.",
        "Healthcare",
    ),
    (
        "Hospital Inpatient Readmission Forecasting Using Clinical EHR Records",
        "Computes 30-day post-discharge readmission probability from diagnosis codes, lab test panels, and length-of-stay histories.",
        "Healthcare",
    ),
    (
        "Parkinson Disease Motor Tremor and Gait Analysis with Wearables",
        "Quantifies bradykinesia, postural instability, and resting hand tremors using tri-axial smartphone gyroscopes and shoe pressure sensors.",
        "Healthcare",
    ),
    (
        "Lung Sound Auscultation Classifier for Pediatric Asthma and Wheeze",
        "Filters electronic stethoscope lung acoustic recordings to distinguish adventitious sounds such as crackles, wheezes, and rhonchi.",
        "Healthcare",
    ),
    (
        "ICU Sepsis Onset Early Warning Telemetry Using Physiologic Time Series",
        "Predicts systemic inflammatory response syndrome and septic shock hours before clinical deterioration using vital sign trends.",
        "Healthcare",
    ),
    (
        "Privacy-Preserving Electronic Health Record Anonymization Framework",
        "Sanitizes clinical narrative discharge notes, masking patient names, addresses, and dates while preserving diagnostic epidemiology.",
        "Healthcare",
    ),
    (
        "Chronic Kidney Disease Staging and Progression Model from Blood Tests",
        "Estimates estimated glomerular filtration rate and serum creatinine trends to classify chronic kidney failure stages.",
        "Healthcare",
    ),
    (
        "Surgical Tool Tracking and Pose Estimation in Minimally Invasive Endoscopy",
        "Tracks laparoscopic forceps and needle drivers in laparoscopic surgical video feeds to monitor operating room workflow.",
        "Healthcare",
    ),
    (
        "Continuous Glucose Monitoring Alert System for Type-1 Diabetic Patients",
        "Analyzes interstitial subcutaneous continuous glucose sensor telemetry to issue predictive nocturnal hypoglycemia alarms.",
        "Healthcare",
    ),
    (
        "Medical Ultrasound Image Speckle Reduction and Shadow Inpainting",
        "Enhances acoustic ultrasound kidney and obstetric scans using generative adversarial denoising networks to improve physician visibility.",
        "Healthcare",
    ),
    (
        "Post-Operative Chronic Pain Tracking and Medication Compliance Mobile App",
        "Logs visual analog pain scale ratings, analgesic intake, and functional mobility milestones during post-surgery orthopedic rehabilitation.",
        "Healthcare",
    ),
    (
        "Genomic Single Nucleotide Polymorphism Analysis for Rare Disease Diagnosis",
        "Filters exome sequencing variant call files against clinical genetics databases to identify pathogenic congenital mutations.",
        "Healthcare",
    ),
    (
        "Neonatal Infant Cry Acoustic Classifier for Pain and Distress Assessment",
        "Classifies newborn baby cry audio spectrographic patterns to differentiate hunger, physical pain, and colic distress in maternity wards.",
        "Healthcare",
    ),
    (
        "Glaucoma Optic Disc and Cup Segmentation in Retinal Fundus Photography",
        "Computes vertical cup-to-disc ratio from retinal ophthalmic photographs to identify early optic nerve head excavation.",
        "Healthcare",
    ),
    (
        "Prosthetic Hand Gesture Control Using Surface Electromyography Sensors",
        "Decodes forearm muscle sEMG motor unit potentials to actuate articulated bionic prosthetic fingers and grips.",
        "Healthcare",
    ),

    # ========================================================
    # 3. Education (26 examples)
    # ========================================================
    (
        "Student Academic Performance Prediction and Grade Analytics Platform",
        "Forecasts end-of-semester course grades and GPA outcomes using student continuous internal evaluations, attendance, and quiz submissions.",
        "Education",
    ),
    (
        "Automated Descriptive Essay Scoring and Grammatical Error Correction",
        "Evaluates written student compositions for topical coherence, vocabulary richness, and grammatical syntax errors using NLP.",
        "Education",
    ),
    (
        "Smart Classroom Attendance Monitoring System Using RFID and Facial Recognition",
        "Logs student lecture presence and class participation using ceiling camera face matching and proximity smart card badges.",
        "Education",
    ),
    (
        "Adaptive Learning Recommendation Engine for Engineering Curriculum",
        "Recommends tailored instructional video modules and practice problems based on individual learner concept mastery gaps.",
        "Education",
    ),
    (
        "Online Examination Portal with AI Automated Cheating and Eye Proctoring",
        "Detects suspicious candidate head movements, multiple faces, background voices, and browser tab switching during remote online tests.",
        "Education",
    ),
    (
        "Undergraduate Student College Dropout Early Warning and Intervention System",
        "Identifies at-risk university students likely to abandon degree programs using demographic factors, GPA dips, and fee payment delays.",
        "Education",
    ),
    (
        "Virtual Physics and Chemistry Laboratory Simulator for Secondary Schools",
        "Provides web-based interactive 3D simulations of optics benches, titration experiments, and electrical circuit breadboards.",
        "Education",
    ),
    (
        "Digital College Library Management and Book Lending Reservation Portal",
        "Catalogs textbook ISBNs, manages student borrowing limits, calculates overdue fines, and handles book reservations.",
        "Education",
    ),
    (
        "Computer Science Curriculum Recommendation Engine Based on Industry Trends",
        "Analyzes tech job postings and GitHub repository skills to suggest modern elective courses for college syllabus committees.",
        "Education",
    ),
    (
        "Gamified Mathematics Practice Platform for Middle School Learners",
        "Engages school pupils in arithmetic, algebra, and geometry through quest-based challenges, badges, and adaptive difficulty levels.",
        "Education",
    ),
    (
        "Reading Assistance and Font Modulation Tool for Dyslexic Pupils",
        "Formats educational text passages with specialized letter spacing, bionic reading weights, and integrated text-to-speech narration.",
        "Education",
    ),
    (
        "Automated Student Programming Assignment Grading and Unit Test Evaluation",
        "Compiles and executes student submitted Python and Java code against hidden test cases, checking cyclomatic complexity and plagiarized logic.",
        "Education",
    ),
    (
        "Student Stress and Cognitive Fatigue Detection During Examinations",
        "Estimates mental workload and examination anxiety from web camera blink rates, posture shifts, and keyboard typing cadence.",
        "Education",
    ),
    (
        "Educational Video Lecture Transcript Indexing and Concept Semantic Search",
        "Transcribes university video recordings and time-indexes spoken concepts so students can jump to specific lecture moments.",
        "Education",
    ),
    (
        "Flashcard Spaced Repetition Learning App with SuperMemo Forgetting Curves",
        "Schedules digital flashcard review intervals based on learner recall difficulty to maximize long-term factual memory retention.",
        "Education",
    ),
    (
        "University Campus Shuttle Tracking and Student Commute Information System",
        "Shows live college bus GPS locations, estimated arrival times, and seat occupancy for student and faculty commuters.",
        "Education",
    ),
    (
        "Student Academic Grievance Redressal and Ticket Escalation Management",
        "Routes student petitions regarding examination re-evaluation, hostel amenities, and academic waivers to university deans.",
        "Education",
    ),
    (
        "Virtual Reality Guided Campus Tour and Historical Archives Explorer",
        "Enables prospective freshmen to tour lecture halls, dormitories, and research laboratories via browser-based 3D walkthroughs.",
        "Education",
    ),
    (
        "University Alumni Mentorship and Career Placement Networking Platform",
        "Matches graduating seniors with working alumni mentors based on career aspirations, industry sectors, and regional chapters.",
        "Education",
    ),
    (
        "Personalized Quiz Generator from Textbook PDF Documents Using NLP",
        "Extracts textbook chapter headings, key sentences, and summary points to automatically generate multiple-choice quizzes.",
        "Education",
    ),
    (
        "Automated Handwritten Exam Answer Sheet Optical Character Recognition",
        "Digitizes handwritten student test booklets, segments answered question numbers, and aligns responses for remote professor grading.",
        "Education",
    ),
    (
        "Parent-Teacher Communication and Student Academic Diary Application",
        "Shares daily school attendance, homework assignments, report cards, and teacher circulars with student guardians.",
        "Education",
    ),
    (
        "Merit and Need-Based Student Scholarship Eligibility Verification Engine",
        "Cross-verifies student family income thresholds, academic percentiles, and documentary proofs against scholarship award criteria.",
        "Education",
    ),
    (
        "Academic Course Prerequisite Dependency Graph Visualizer for Students",
        "Visualizes university curriculum syllabus chains to ensure students register for foundational math and science courses in sequence.",
        "Education",
    ),
    (
        "Classroom Acoustic Noise Level Monitoring and Decibel Alert Beacon",
        "Measures classroom background ambient noise to encourage quiet study environments in shared university reading rooms.",
        "Education",
    ),
    (
        "Interactive Sign Language Vocabulary Tutor for Hearing-Impaired Students",
        "Teaches finger spelling and deaf sign language gestures using webcam feedback and skeleton hand tracking neural models.",
        "Education",
    ),

    # ========================================================
    # 4. Finance (26 examples)
    # ========================================================
    (
        "Credit Card Fraud Detection System Using Random Forest and Autoencoders",
        "Identifies unauthorized payment transactions in high-volume credit card streams using anomaly scores and classifier ensembles.",
        "Finance",
    ),
    (
        "Stock Market Price Trend Prediction Using Time Series LSTM Networks",
        "Forecasts equity share closing valuations and intraday price volatility from historical ticker bars and macroeconomic indicators.",
        "Finance",
    ),
    (
        "Automated Loan Eligibility Prediction and Underwriting Risk Assessment",
        "Evaluates personal and mortgage loan applicant creditworthiness from income, debt-to-income ratios, and bureau credit histories.",
        "Finance",
    ),
    (
        "Cryptocurrency Portfolio Asset Allocation and Volatility Forecasting Tool",
        "Optimizes digital asset weightings using mean-variance portfolio theory and Value-at-Risk simulations across decentralized tokens.",
        "Finance",
    ),
    (
        "Personal Expense Tracker and Smart Budget Advisory Mobile App",
        "Categorizes bank SMS alerts and debit transactions, generating monthly spending breakdowns and savings goal recommendations.",
        "Finance",
    ),
    (
        "Algorithmic Trading Bot Based on Technical Indicators and News Sentiment",
        "Executes automated buy and sell orders on brokerage exchange APIs based on moving average convergence divergence and news sentiment.",
        "Finance",
    ),
    (
        "Microfinance Alternative Credit Scoring for Rural and Unbanked Borrowers",
        "Computes micro-loan creditworthiness from utility payment consistency, mobile phone airtime recharges, and smallholder trade receipts.",
        "Finance",
    ),
    (
        "Retail Bank Customer Churn Prediction and Attrition Retention Model",
        "Predicts depositors likely to close savings accounts or cancel credit lines using transaction frequencies and tenure data.",
        "Finance",
    ),
    (
        "Accounts Payable Invoice Information Extraction and Matching Using OCR",
        "Extracts vendor line items, invoice numbers, tax values, and dates from PDF receipts to perform three-way purchase order matching.",
        "Finance",
    ),
    (
        "Blockchain-Based Peer-to-Peer Micro Lending and Smart Contract Escrow",
        "Enables direct lending between individuals with automated interest payments and collateral liquidation managed via Ethereum smart contracts.",
        "Finance",
    ),
    (
        "Automobile Insurance Claim Fraud Pattern Recognition System",
        "Detects staged accident claims, inflated body repair estimates, and recurring claimant rings using relational graph analytics.",
        "Finance",
    ),
    (
        "Corporate Bankruptcy and Financial Distress Early Warning Indicator",
        "Forecasts commercial firm solvency and chapter 11 bankruptcy risk from Altman Z-score ratios and quarterly balance sheets.",
        "Finance",
    ),
    (
        "Foreign Currency Exchange Rate Forecasting with Recurrent Neural Networks",
        "Predicts major currency pairs like EUR/USD and GBP/USD using international interest rate differentials and central bank news sentiment.",
        "Finance",
    ),
    (
        "Real-Time Point-of-Sale Payment Gateway Transaction Anomaly Detector",
        "Screens merchant terminal debit transactions in real time to intercept cloned magnetic stripe cards and velocity attacks.",
        "Finance",
    ),
    (
        "Financial News Sentiment Analysis and Market Impact Predictor",
        "Scrapes financial press releases and earnings call transcripts to compute corporate market sentiment scores.",
        "Finance",
    ),
    (
        "Automated Income Tax Deduction Optimizer and Filing Assistant",
        "Calculates individual tax liabilities, identifying optimal savings deductions under regional tax code schedules.",
        "Finance",
    ),
    (
        "Retirement Pension Wealth Accumulation and Annuity Simulator",
        "Models 30-year retirement nest egg growth under diverse inflation, bond yield, and equity returns using Monte Carlo simulations.",
        "Finance",
    ),
    (
        "Mortgage Interest Rate Forecast Model Based on Central Bank Yield Curves",
        "Estimates residential mortgage borrowing rate trends from central bank treasury yields and inflation expectations.",
        "Finance",
    ),
    (
        "Enterprise Financial Ledger Audit Anomaly Detection with Machine Learning",
        "Audits general ledger journal entries to uncover unusual off-hours postings, rounded amounts, and unauthorized account adjustments.",
        "Finance",
    ),
    (
        "Decentralized Liquidity Pool and Automated Market Maker Analytics",
        "Tracks impermanent loss, liquidity pool token yields, and slippage fees across decentralized cryptocurrency exchanges.",
        "Finance",
    ),
    (
        "Anti-Money Laundering Suspicious Activity Transaction Graph Network",
        "Detects smurfing, layered wire transfers, and shell company fund routing using graph neural network link prediction.",
        "Finance",
    ),
    (
        "Consumer Credit Card Line Limit Recommendation Engine",
        "Recommends proactive credit limit increases or reductions based on cardholder revolving balance habits and payment stability.",
        "Finance",
    ),
    (
        "Commercial Bank ATM Cash Inventory Replenishment Optimization",
        "Forecasts cash withdrawal volumes across urban branch automated teller machines to minimize idle cash holding costs.",
        "Finance",
    ),
    (
        "Supply Chain Reverse Factoring and Early Invoice Payment Discounting",
        "Connects suppliers and corporate buyers on a marketplace where suppliers sell accounts receivable at competitive discount rates.",
        "Finance",
    ),
    (
        "Mobile Banking Voice Biometrics and Transaction Authentication",
        "Verifies telephone and mobile app banking customer identities through acoustic vocal tract speaker verification.",
        "Finance",
    ),
    (
        "Robo-Advisory Wealth Management and Automated Asset Rebalancing",
        "Allocates retail investor mutual funds into diversified index ETFs and triggers automated tax-loss harvesting rebalancing.",
        "Finance",
    ),

    # ========================================================
    # 5. Cybersecurity (26 examples)
    # ========================================================
    (
        "Network Intrusion Detection System Using Deep Autoencoders and Packet Sniffing",
        "Inspects TCP/IP packet header streams to detect port scans, SYN floods, and unauthorized subnet penetration attempts.",
        "Cybersecurity",
    ),
    (
        "Phishing Website Detection Using URL Lexical Analysis and Machine Learning",
        "Identifies malicious spoofed banking and login web addresses using domain length, entropy, and registrar WHOIS features.",
        "Cybersecurity",
    ),
    (
        "Malware Classification and Signature Analysis from Windows PE Binaries",
        "Classifies trojans, worms, and spyware by inspecting imported DLL functions, section headers, and byte histograms of executable files.",
        "Cybersecurity",
    ),
    (
        "DDoS Attack Mitigation and Anomaly Detection in Software-Defined Networks",
        "Detects distributed denial-of-service traffic spikes in OpenFlow controller switches and rate-limits malicious source IP subnets.",
        "Cybersecurity",
    ),
    (
        "Password Strength Estimator and Breach Notification Service",
        "Evaluates password cracking resistance using zxcvbn entropy heuristics and alerts users if credentials appear in compromised database dumps.",
        "Cybersecurity",
    ),
    (
        "End-to-End Zero-Knowledge Encrypted Cloud Storage Vault",
        "Secures user files client-side using AES-GCM-256 before uploading to cloud buckets, ensuring the storage provider has zero decryption keys.",
        "Cybersecurity",
    ),
    (
        "Ransomware Early Detection System via File System Activity Monitoring",
        "Intercepts rapid file rename and mass symmetric encryption operations in user directories to kill malicious processes.",
        "Cybersecurity",
    ),
    (
        "Web Application Firewall with Automated SQL Injection Pattern Filtering",
        "Inspects HTTP POST parameters and cookies to block SQL syntax injections, command execution payloads, and cross-site scripts.",
        "Cybersecurity",
    ),
    (
        "Automated Vulnerability Assessment and Penetration Testing Dashboard",
        "Scans network subnets for unpatched CVE security flaws, open ports, default credentials, and insecure SSL/TLS configurations.",
        "Cybersecurity",
    ),
    (
        "Multi-Factor Authentication System Using Biometrics and Time-Based Tokens",
        "Enforces enterprise security login policies using FIDO2 WebAuthn fingerprint keys and RFC 6238 TOTP authenticator codes.",
        "Cybersecurity",
    ),
    (
        "IoT Firmware Binary Vulnerability Analyzer and Hardcoded Key Extractor",
        "Decompiles smart home device router firmware images to detect hardcoded root passwords and unpatched busybox binaries.",
        "Cybersecurity",
    ),
    (
        "Distributed Honeypot Threat Intelligence Aggregator for Attack Attribution",
        "Deploys low-interaction decoy SSH and Telnet servers across cloud regions to log attacker IP geolocations and brute-force dictionaries.",
        "Cybersecurity",
    ),
    (
        "ARP Cache Poisoning and Man-in-the-Middle Detection in Enterprise LANs",
        "Monitors local broadcast Ethernet traffic to spot duplicated MAC addresses and unauthorized gateway ARP spoofing attacks.",
        "Cybersecurity",
    ),
    (
        "Spam Email Filtering and Header Spoofing Detector Using NLP",
        "Classifies unsolicited spam and spear-phishing emails by analyzing DKIM, SPF, and DMARC headers along with email body tokens.",
        "Cybersecurity",
    ),
    (
        "Dark Web Credential Leak Alert and Threat Intelligence Notification",
        "Monitors onion paste sites and underground hacker forums to notify corporate administrators regarding leaked company employee credentials.",
        "Cybersecurity",
    ),
    (
        "Blockchain-Based Decentralized DNS Against Cache Poisoning",
        "Stores domain name IP mappings in an immutable public ledger to prevent DNS spoofing, BGP hijacking, and rogue nameserver redirection.",
        "Cybersecurity",
    ),
    (
        "Digital Image Steganography and Hidden Payload Detection Tool",
        "Detects secret data embedded into JPEG and PNG image least-significant bits using spatial rich model steganalysis.",
        "Cybersecurity",
    ),
    (
        "Keystroke Dynamics Biometric Continuous User Authentication",
        "Authenticates workstation operators continuously based on keyboard flight time and key-hold duration typing rhythms.",
        "Cybersecurity",
    ),
    (
        "Kubernetes Container Runtime Security and Escaped Process Monitoring",
        "Monitors eBPF Linux syscalls inside Docker containers to detect privilege escalation, shell spawning, and container escapes.",
        "Cybersecurity",
    ),
    (
        "Android Mobile App Reverse Engineering and Code Tampering Protection",
        "Injects anti-debugging hooks, root detection checks, and Dex bytecode integrity verification into Android mobile application packages.",
        "Cybersecurity",
    ),
    (
        "Privilege Escalation Detection in Linux Kernel Syslog Streams",
        "Analyzes auditd system calls to flag unauthorized sudo usage, SUID binary execution, and dirty COW kernel exploit attempts.",
        "Cybersecurity",
    ),
    (
        "DNS Tunneling Data Exfiltration Detection Using Query Entropy",
        "Identifies covert malware data exfiltration over base64-encoded DNS subdomains using Shannon entropy calculations on query strings.",
        "Cybersecurity",
    ),
    (
        "Automated Cross-Site Scripting (XSS) Vulnerability Sanitizer",
        "Inspects web application frontend templates and dynamic DOM manipulations to neutralize reflected and stored XSS vulnerabilities.",
        "Cybersecurity",
    ),
    (
        "Zero-Trust Network Access Identity Proxy for Microservices",
        "Authenticates service-to-service API calls using mutual TLS certificates and short-lived JSON Web Token claims.",
        "Cybersecurity",
    ),
    (
        "AWS S3 Cloud Storage Bucket Misconfiguration and Public Leak Scanner",
        "Scans enterprise Amazon Web Services cloud assets for unencrypted S3 buckets, overly permissive IAM policies, and exposed keys.",
        "Cybersecurity",
    ),
    (
        "Deep Packet Inspection for Tor and Encrypted Proxy Traffic Identification",
        "Analyzes packet size distributions, flow inter-arrival times, and TLS handshake ciphers to detect anonymized proxy and VPN tunnels.",
        "Cybersecurity",
    ),

    # ========================================================
    # 6. Web Applications (26 examples)
    # ========================================================
    (
        "Online Shopping Management System and E-Commerce Web Portal",
        "Full-stack web store featuring product search filters, shopping cart persistence, payment gateway integration, and order shipping management.",
        "Web Applications",
    ),
    (
        "Movie Recommendation System Using Collaborative and Content-Based Filtering",
        "Recommends films and TV shows to users based on star ratings, favorite cast members, genres, and matrix factorization.",
        "Web Applications",
    ),
    (
        "Product Demand Prediction and Inventory Optimization Portal",
        "Web-based supply chain dashboard forecasting retail product demand to prevent stockouts and warehouse holding costs.",
        "Web Applications",
    ),
    (
        "Travel Itinerary Planning and Group Tour Reservation Web Platform",
        "Enables tourists to build custom daily sightseeing schedules, calculate budget estimates, and book shared excursions.",
        "Web Applications",
    ),
    (
        "Full-Stack Social Media Platform with Real-Time Chat and Notifications",
        "Web community application supporting user profiles, photo sharing, thread comments, WebSocket instant messaging, and activity feeds.",
        "Web Applications",
    ),
    (
        "Online Food Delivery Platform with Real-Time GPS Rider Tracking and Dispatch",
        "Connects local restaurants with customers, featuring digital menus, live courier location tracking, and delivery dispatch.",
        "Web Applications",
    ),
    (
        "Real Estate Property Rental Listing Portal with Interactive Maps",
        "Enables landlords and tenants to browse verified apartment rentals with neighborhood search filters, map pins, and virtual leases.",
        "Web Applications",
    ),
    (
        "Online Event Management and Ticket Booking System with QR Code Validation",
        "Handles conference and concert ticket purchases, seat reservations, digital ticketing, and entrance scanning via smartphone cameras.",
        "Web Applications",
    ),
    (
        "Freelancer Job Marketplace and Escrow Milestone Payment Platform",
        "Facilitates remote freelance contracts, proposal bids, milestone deliverables, client reviews, and escrow fund releases.",
        "Web Applications",
    ),
    (
        "Cloud-Based Collaborative Document Editor with Real-Time Markdown Sync",
        "Provides simultaneous multi-user text editing with operational transformation, version history diffing, and export to PDF.",
        "Web Applications",
    ),
    (
        "Restaurant Table Reservation and Waitlist Management Web Application",
        "Manages dining room floor seating plans, customer reservations, and SMS waitlist notifications during peak dining hours.",
        "Web Applications",
    ),
    (
        "Used Car Price Valuation and Peer-to-Peer Automobile Marketplace",
        "Estimates fair market vehicle valuations based on odometer mileage, year, make, and condition to facilitate direct used car sales.",
        "Web Applications",
    ),
    (
        "Customer Support Helpdesk and Automated Ticket Routing Portal",
        "Manages customer service support inquiries, categorizing incoming emails into agent priority queues with SLA timers.",
        "Web Applications",
    ),
    (
        "Gym Membership Management and Group Fitness Class Booking Portal",
        "Allows fitness club members to reserve workout timeslots, renew monthly subscriptions, and track attendance at spin and yoga classes.",
        "Web Applications",
    ),
    (
        "Digital Art NFT Showcase and Smart Contract Auction Platform",
        "Web gallery for digital creators to mint cryptographic art tokens, set reserve prices, and manage peer-to-peer bidding auctions.",
        "Web Applications",
    ),
    (
        "Culinary Recipe Search and Grocery Ingredient Shopping List Generator",
        "Recommends cooking recipes based on available pantry items and aggregates missing ingredients into categorized grocery checklists.",
        "Web Applications",
    ),
    (
        "Podcast Audio Streaming Platform with Episode Playlist Management",
        "Web audio player supporting RSS podcast feed subscriptions, playback speed toggles, episode bookmarking, and creator analytics.",
        "Web Applications",
    ),
    (
        "Community Lost and Found Portal with Image Similarity Matching",
        "Helps users locate misplaced pets and personal belongings by comparing uploaded photograph features and geographic tags.",
        "Web Applications",
    ),
    (
        "Pet Adoption and Animal Rescue Shelter Database Web Portal",
        "Connects animal rescue shelters with adopting families, showcasing dog and cat profiles, medical history, and adoption applications.",
        "Web Applications",
    ),
    (
        "Hotel Room Booking and Tariff Comparison Web Engine",
        "Aggregates room rates, guest amenities, customer reviews, and cancellation policies across boutique and chain hotels.",
        "Web Applications",
    ),
    (
        "Blood Donor Volunteer Network and Hospital Emergency Request Portal",
        "Connects voluntary blood donors with regional hospitals based on blood group compatibility and urgent geographic proximity.",
        "Web Applications",
    ),
    (
        "Smart Parking Slot Reservation Web Application with Payment Gateway",
        "Enables drivers to locate and reserve parking bays in commercial downtown parking garages before commencing their journey.",
        "Web Applications",
    ),
    (
        "Local Home Service Provider Directory and Verified Review Marketplace",
        "Connects homeowners with certified local electricians, plumbers, and carpenters with upfront pricing and verified reviews.",
        "Web Applications",
    ),
    (
        "SaaS Subscription Billing and Recurring Invoice Management Web App",
        "Automates software subscription renewals, proration calculations, customer credit card charging, and dunning management.",
        "Web Applications",
    ),
    (
        "Collaborative Music Playlist Sharing and Social Listening Room",
        "Enables online groups of friends to curate shared song queues, vote on tracks, and listen to synchronized web audio streams.",
        "Web Applications",
    ),
    (
        "Applicant Tracking System and Resume Parsing Portal for Recruiters",
        "Extracts candidate contact details, work history, and educational degrees from uploaded resumes to manage corporate hiring pipelines.",
        "Web Applications",
    ),

    # ========================================================
    # 7. Other (26 examples: Transportation, Environment, Robotics, IoT)
    # ========================================================
    (
        "Smart Traffic Light Optimization System Using Vehicle Density Sensors",
        "Regulates urban traffic junction green light durations dynamically based on live vehicle queue lengths from inductive loop sensors.",
        "Other",
    ),
    (
        "Automated Conveyor Waste Sorting and Recyclable Material Classification",
        "Classifies plastics, paper, and metal cans on municipal recycling conveyor belts using optical cameras and pneumatic rejector jets.",
        "Other",
    ),
    (
        "Autonomous Search and Rescue Drone Navigation in Disaster Zones",
        "Guides aerial quadcopters across collapsed structures without GPS, utilizing visual odometry and obstacle avoidance lidar sensors.",
        "Other",
    ),
    (
        "Urban Air Quality Index Monitoring and PM2.5 Pollution Forecasting",
        "Monitors particulate matter, nitrogen dioxide, and ozone concentrations across city sensor nodes to predict 24-hour smog levels.",
        "Other",
    ),
    (
        "Seismic Earthquake Early Warning System Using Distributed Accelerometers",
        "Detects primary seismic P-waves from low-cost ground vibration sensors to broadcast automated sirens seconds before destructive S-waves arrive.",
        "Other",
    ),
    (
        "Solar Panel Dual-Axis Sun Tracking System with Output Optimization",
        "Drives servo motors to orient photovoltaic solar panels perpendicular to the sun throughout the day, maximizing kilowatt electrical output.",
        "Other",
    ),
    (
        "Acoustic Water Pipeline Leakage Detection System Using Pressure Sensors",
        "Pinpoints underground municipal water pipe fractures and bursts by analyzing sound frequency signatures and hydrophone pressure waves.",
        "Other",
    ),
    (
        "Smart Street Lighting System with Infrared Vehicle Motion Detection",
        "Dims highway street lamps to energy-saving low power when empty and brightens illumination when approaching vehicles are detected.",
        "Other",
    ),
    (
        "Offline Voice Command Home Automation Hub with Edge AI Processing",
        "Executes domestic lighting, fan, and thermostat voice commands locally on a Raspberry Pi without transmitting audio to cloud servers.",
        "Other",
    ),
    (
        "3D Object Scanner and Point Cloud Reconstruction from Stereo Vision",
        "Captures physical artifact geometry using structured light laser triangulation, converting surface points into 3D CAD meshes.",
        "Other",
    ),
    (
        "Wildfire Spread Simulation and Evacuation Route Planner",
        "Simulates forest fire propagation across hilly terrain using wind velocity, slope, and vegetation moisture cellular automata models.",
        "Other",
    ),
    (
        "Autonomous Underwater Submarine Sonar Navigation for Coral Reef Mapping",
        "Navigates marine bathymetric terrain autonomously using acoustic Doppler velocity logs and sidescan sonar mapping.",
        "Other",
    ),
    (
        "Bridge Structural Health Monitoring Using Accelerometers and Strain Gauges",
        "Measures dynamic bridge deck vibrations and thermal expansion stresses under heavy vehicular traffic to flag structural fatigue.",
        "Other",
    ),
    (
        "Wind Turbine Blade Crack and Surface Erosion Detection Using Thermography",
        "Inspects commercial wind turbine rotor blades for composite delamination using drone infrared thermal cameras.",
        "Other",
    ),
    (
        "Municipal River Flood Level Telemetry and Early Warning Broadcast System",
        "Monitors river discharge rates and ultrasonic water levels to issue automated SMS alerts to low-lying floodplain communities.",
        "Other",
    ),
    (
        "Railway Track Crack and Obstacle Detection Inspection Vehicle",
        "Scans steel rail continuity using ultrasonic eddy current probes and camera vision to prevent train derailments.",
        "Other",
    ),
    (
        "High-Rise Elevator Group Dispatching Optimization with Passenger Traffic",
        "Dispatches elevator cabs in skyscrapers using fuzzy logic and genetic algorithms to minimize passenger waiting times.",
        "Other",
    ),
    (
        "Electric Vehicle Battery State-of-Health and Remaining Range Estimator",
        "Estimates lithium-ion battery pack degradation, internal resistance, and driving range from cell voltage and temperature profiles.",
        "Other",
    ),
    (
        "Smart Waste Bin Fill Level Monitoring Using LoRaWAN Telemetry",
        "Measures garbage bin fill heights using ultrasonic sensors, transmitting battery-efficient LoRaWAN packets to optimize municipal collection routes.",
        "Other",
    ),
    (
        "Stadium Crowd Density Estimation and Emergency Evacuation Bottleneck Simulator",
        "Monitors spectator stadium concourse crowd flow to identify bottleneck gates and simulate rapid evacuation procedures.",
        "Other",
    ),
    (
        "Industrial Induction Motor Bearing Fault Diagnosis from Vibration Spectra",
        "Detects inner and outer race ball bearing fatigue spalling in manufacturing motors by analyzing FFT frequency spectra.",
        "Other",
    ),
    (
        "Airport Runway Foreign Object Debris Radar Detection System",
        "Scans airport takeoff runways with millimeter-wave radar to detect loose metal bolts, stone fragments, and tire debris.",
        "Other",
    ),
    (
        "Industrial Carbon Footprint and Greenhouse Gas Emission Calculator",
        "Aggregates factory electrical utility bills, fossil fuel usage, and logistics freight mileage into scope 1, 2, and 3 carbon metric tons.",
        "Other",
    ),
    (
        "Satellite Remote Sensing for Illegal Deforestation and Logging Tracking",
        "Detects canopy loss in protected tropical rainforests by comparing bi-weekly multispectral satellite imagery.",
        "Other",
    ),
    (
        "Autonomous Warehouse AGV Fleet Controller and Collision-Free Path Planning",
        "Coordinates wheeled automated guided vehicles transporting pallet racks in logistics warehouses using A-star path routing.",
        "Other",
    ),
    (
        "Smart Water Meter Consumption Telemetry and Continuous Leak Alarm",
        "Detects continuous trickle leaks in residential plumbing by analyzing smart flow meter pulse rates during midnight baseline periods.",
        "Other",
    ),
]
