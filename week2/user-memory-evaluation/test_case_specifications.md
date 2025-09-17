# User Memory Evaluation Test Case Specifications

## Overview
This document defines the comprehensive structure for all 60 test cases across three evaluation layers. Each test case represents realistic US business scenarios with authentic conversational complexity.

## Test Case Requirements

### Universal Requirements (All Layers)
- **Minimum 50 rounds** (100+ messages) per conversation
- **Authentic US business scenarios** representing real services
- **Intentional complexity** including:
  - Confusing and irrelevant information
  - Back-and-forth corrections
  - Changed decisions
  - Tangential discussions
  - Multiple options discussed but not chosen

### Layer 1: Basic Recall & Direct Retrieval (20 test cases)
**Structure**: Single conversation history per test case
**Focus**: Direct information retrieval without ambiguity
**Evaluation**: Can the agent accurately retrieve specific factual information?

#### Completed Test Cases (10/20):
1. `layer1_01_bank_account` - Bank account setup with account numbers
2. `layer1_02_insurance_claim` - Auto insurance claim details
3. `layer1_03_medical_appointment` - Healthcare appointment scheduling
4. `layer1_04_airline_booking` - Flight reservation details
5. `layer1_05_internet_service` - Internet/cable installation
6. `layer1_06_credit_card_app` - Credit card application
7. `layer1_07_car_rental` - Car rental reservation
8. `layer1_08_hotel_reservation` - Hotel booking details
9. `layer1_09_home_security` - Security system installation
10. `layer1_10_pharmacy_transfer` - Prescription transfer

#### Remaining Test Cases (11-20):
11. **Mortgage Application** - Loan details, rates, closing dates
12. **Tax Preparation** - Appointment details, document requirements
13. **Gym Membership** - Contract terms, trainer sessions
14. **Pet Services** - Vet appointments, boarding reservations
15. **Home Warranty** - Coverage details, claim numbers
16. **Restaurant Event** - Catering order, event details
17. **Moving Service** - Quote details, moving date
18. **Dental Treatment** - Treatment plan, insurance coverage
19. **College Application** - Deadlines, requirements, ID numbers
20. **Retirement Account** - 401k details, beneficiaries

### Layer 2: Contextual Reasoning & Disambiguation (20 test cases)
**Structure**: Multiple conversation histories per test case (2-3 conversations)
**Focus**: Disambiguation when user makes ambiguous requests
**Evaluation**: Does agent retrieve ALL relevant information and ask for clarification?

#### Completed Test Cases (3/20):
1. `layer2_01_multiple_vehicles` - Two cars, ambiguous "my car" reference
2. `layer2_02_multiple_properties` - Primary home and rental property
3. `layer2_03_multiple_credit_cards` - Different cards with different benefits

#### Remaining Test Cases (4-20):
4. **Multiple Bank Accounts** - Checking, savings, business accounts
5. **Family Insurance Plans** - Individual vs family members' coverage
6. **Multiple Prescriptions** - Different medications, dosages, pharmacies
7. **Several Subscriptions** - Streaming, software, magazines
8. **Multiple Flights** - Business and personal trips booked
9. **Different Phone Lines** - Personal, business, family plan
10. **Various Investment Accounts** - IRA, 401k, brokerage
11. **Multiple Loans** - Mortgage, auto, personal loans
12. **Several Rental Properties** - Different tenants and issues
13. **Multiple Pets** - Different vets, medications, appointments
14. **Various Home Services** - Lawn, pool, cleaning services
15. **Different Warranties** - Electronics, appliances, vehicles
16. **Multiple Children** - School, medical, activity schedules
17. **Several Doctors** - Primary, specialists, dentist
18. **Different Projects** - Home renovation, work projects
19. **Multiple Reservations** - Hotels, restaurants, events
20. **Various Insurance Claims** - Auto, home, health

### Layer 3: Cross-Session Synthesis & Proactive Assistance (20 test cases)
**Structure**: Multiple conversation histories from different time periods (3-4 conversations)
**Focus**: Proactive identification of issues by connecting disparate information
**Evaluation**: Can agent synthesize across time and context to provide proactive warnings?

#### Completed Test Cases (2/20):
1. `layer3_01_travel_coordination` - Passport expiration before booked travel
2. `layer3_02_medical_insurance_coordination` - Surgery costs and preparation

#### Remaining Test Cases (3-20):
3. **Tax Document Collection** - Gathering from multiple sources for filing
4. **Warranty Expiration** - Product failure after warranty discussed months ago
5. **Insurance Gap** - New purchase not covered by existing policy
6. **Prescription Refill** - Doctor retirement affecting renewal
7. **Credit Card Fraud Pattern** - Charges at previously mentioned compromised merchant
8. **Home Sale Coordination** - Mortgage, moving, utilities across conversations
9. **Student Loan Forgiveness** - Eligibility from employment history
10. **Medical Test Follow-up** - Missed follow-up from previous appointment
11. **Contract Renewal** - Service changes affecting old contract terms
12. **Travel Visa Requirements** - New requirements for previously booked destination
13. **Investment Rebalancing** - Market changes affecting stated goals
14. **Insurance Claim Impact** - Rate increase from previous claim
15. **Benefit Enrollment** - Life changes affecting coverage needs
16. **Property Tax** - Assessment change from mentioned renovations
17. **Retirement Planning** - 401k changes affecting retirement date
18. **Estate Planning** - New assets requiring will updates
19. **Business License** - Renewal needed based on business start date
20. **Vehicle Registration** - Expiration based on purchase date

## Conversation Complexity Requirements

### Information Density
Each conversation must include:
- **5-10 key pieces of information** that might be queried
- **15-20 pieces of irrelevant detail** for confusion
- **3-5 corrections or changes** during the conversation
- **2-3 tangential topics** discussed but not pursued

### Realistic Elements
- **Business hours and availability** discussions
- **Price negotiations** and comparisons
- **Technical difficulties** ("Can you hear me?" "Let me look that up")
- **Hold times** ("Let me transfer you", "One moment please")
- **Clarifications** ("Did you say X or Y?")
- **Options presented but declined**
- **Future considerations** ("Maybe later", "I'll think about it")

### Common Confusions to Include
- Similar sounding numbers/codes
- Multiple reference numbers (confirmation, account, transaction)
- Date changes and rescheduling
- Price adjustments and discounts discovered mid-conversation
- Correcting previous statements
- Mishearing and clarification
- System limitations ("I can't do that, but...")

## Evaluation Criteria Structure

### Layer 1 Criteria
- Single piece of unambiguous information
- Clear success/failure indicators
- No interpretation required

### Layer 2 Criteria  
- Multiple valid answers requiring ALL to be retrieved
- Disambiguation requirements
- Clear indication when clarification is needed

### Layer 3 Criteria
- Synthesis requirements across conversations
- Temporal reasoning (X before Y)
- Proactive identification of issues
- Priority ordering of concerns

## Business Domains Coverage

### Financial Services (15 test cases)
- Banking, credit cards, loans, investments, insurance

### Healthcare (10 test cases)
- Medical appointments, prescriptions, insurance, dental, vision

### Travel & Hospitality (8 test cases)
- Airlines, hotels, car rentals, cruise, travel insurance

### Home Services (10 test cases)
- Internet, utilities, repairs, security, warranty

### Retail & Services (10 test cases)
- Shopping, subscriptions, deliveries, returns

### Professional Services (7 test cases)
- Legal, tax, real estate, education, consulting

## Implementation Notes

### Conversation Generation Guidelines
1. Start with friendly greeting and agent introduction
2. Build context gradually through natural dialogue
3. Include system/process explanations
4. Add realistic interruptions and tangents
5. Incorporate hold/wait scenarios
6. Include verification and security questions
7. End with summary and confirmation

### Common Patterns to Reuse
- Security verification flows
- Payment processing discussions
- Scheduling availability checks
- Insurance coverage explanations
- Technical troubleshooting steps
- Options comparison discussions
- Terms and conditions reviews

### Quality Checklist
- [ ] Minimum 50 conversation rounds
- [ ] Key information clearly stated
- [ ] Sufficient confusing information included
- [ ] Multiple corrections/changes present
- [ ] Realistic business scenario
- [ ] Natural dialogue flow
- [ ] Clear evaluation criteria
- [ ] Appropriate layer complexity
