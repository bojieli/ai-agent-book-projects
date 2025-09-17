# User Memory Evaluation Framework Guide

## Overview
This framework provides a comprehensive three-layer evaluation system for testing AI agents' memory capabilities, progressing from basic recall to complex cross-session synthesis.

## Test Structure

### Total Test Cases: 60
- **Layer 1**: 20 test cases (Basic Recall)
- **Layer 2**: 20 test cases (Context Reasoning) 
- **Layer 3**: 20 test cases (Cross-session Synthesis)

## Layer Descriptions

### Layer 1: Basic Recall & Direct Retrieval
**Purpose**: Test fundamental memory storage and retrieval of explicit, unambiguous information.

**Characteristics**:
- Single conversation history per test
- Direct, factual questions
- Clear, structured information
- No ambiguity or inference required

**Example Scenarios**:
1. Bank account setup details
2. Insurance claim information
3. Medical appointment scheduling
4. Airline booking details
5. Internet service configuration
6. Credit card application
7. Car rental reservation
8. Hotel booking
9. Home security installation
10. Pharmacy prescription transfer
11. Mortgage application details
12. Gym membership terms
13. Tax preparation data
14. Cell phone upgrade
15. College enrollment
16. Home renovation quotes
17. Veterinary care plans
18. Retirement planning
19. Wedding venue booking
20. Daycare enrollment

**Evaluation Focus**: Exact recall of specific details (numbers, dates, names, amounts)

### Layer 2: Context Reasoning & Disambiguation
**Purpose**: Test ability to handle ambiguous requests and retrieve ALL relevant information from multiple similar items.

**Characteristics**:
- Multiple conversation histories (3-4 per test)
- Similar items requiring disambiguation
- Ambiguous user queries
- Need to identify and present all options

**Example Scenarios**:
1. Multiple vehicles (insurance/maintenance)
2. Multiple properties (rental/primary)
3. Multiple credit cards
4. Multiple streaming subscriptions
5. Multiple bank accounts
6. Multiple insurance policies
7. Multiple family members' medical records
8. Multiple rental properties
9. Multiple children's school information
10. Multiple loyalty programs
11. Multiple home service contracts
12. Multiple investment portfolios
13. Multiple travel bookings
14. Multiple warranty registrations
15. Multiple prescription medications
16. Multiple business accounts
17. Multiple gym memberships
18. Multiple pet services
19. Multiple delivery addresses
20. Multiple phone lines

**Evaluation Focus**: Retrieving ALL relevant information, not randomly selecting one option

### Layer 3: Cross-session Synthesis & Proactive Assistance
**Purpose**: Test ability to synthesize information across multiple sessions and provide proactive, predictive assistance.

**Characteristics**:
- Multiple conversation histories (4+ per test)
- Information spread across time and contexts
- Requires pattern recognition and inference
- Proactive recommendations expected

**Example Scenarios**:
1. Travel coordination (passport expiry + flight booking)
2. Medical-insurance coordination
3. Home purchase coordination
4. Tax preparation synthesis
5. Emergency preparedness
6. Education planning
7. Estate planning
8. Healthcare coordination
9. Vehicle maintenance planning
10. Seasonal preparation
11. Budget optimization
12. Family event coordination
13. Subscription audit
14. Insurance gap analysis
15. Loyalty program optimization
16. Contract renewal opportunities
17. Health screening reminders
18. Financial milestone tracking
19. Property management coordination
20. Business expense categorization

**Evaluation Focus**: Proactive synthesis, pattern recognition, predictive assistance

## Test Case Structure

Each YAML test case contains:

```yaml
test_id: [layer]_[number]_[descriptor]
category: [layer1|layer2|layer3]
title: [Descriptive title]
description: [Test objective]
conversation_histories:
  - conversation_id: [unique_id]
    timestamp: [ISO datetime]
    metadata:
      business: [Company name]
      department: [Department]
      call_duration: [Duration]
    messages:
      - role: [user|assistant]
        content: [Message content]
      # ... 50+ rounds minimum
user_question: [Question for evaluation]
evaluation_criteria: |
  [Detailed criteria for LLM judge]
```

## Conversation Requirements

### Minimum Length
- Each conversation MUST have at least 50 rounds (25 user + 25 assistant)
- Represents realistic, prolonged phone conversations

### Content Characteristics
1. **Detailed Information**: Names, numbers, dates, specific terms
2. **Intentional Confusion**: Similar items, corrections, clarifications
3. **Realistic Flow**: Natural digressions, back-references, context switches
4. **Progressive Disclosure**: Information revealed gradually
5. **Corrections**: User/agent corrections of earlier statements

## Evaluation Methodology

### LLM as Judge Approach
- Use a capable LLM (e.g., Claude, GPT-4, Kimi K1) to evaluate responses
- Never use exact string matching
- Focus on semantic understanding and completeness

### Evaluation Criteria Examples

**Layer 1**: "The agent should correctly recall that the mortgage down payment was $125,000 (20% of $625,000 purchase price), coming from Wells Fargo ($67,000) and Marcus ($45,000) savings accounts."

**Layer 2**: "The agent must retrieve information about ALL three vehicles (Tesla Model Y, Honda CR-V, BMW X5) and ask which one needs service, not randomly select one."

**Layer 3**: "The agent should recognize the passport expires in February 2025, the Japan trip is in January 2025, and proactively warn about the 6-month validity requirement."

## Implementation Interface

```python
class MemoryEvaluationFramework:
    def list_test_cases(self, layer: Optional[int] = None) -> List[TestCase]:
        """List all available test cases, optionally filtered by layer"""
        pass
    
    def get_test_case(self, test_id: str) -> TestCase:
        """Retrieve a specific test case"""
        pass
    
    def get_conversation_histories(self, test_id: str) -> List[Conversation]:
        """Get all conversation histories for a test case"""
        pass
    
    def get_user_question(self, test_id: str) -> str:
        """Get the evaluation question for the test case"""
        pass
    
    def evaluate_response(self, test_id: str, agent_response: str) -> EvaluationResult:
        """Evaluate agent's response using LLM judge"""
        pass
```

## Usage Example

```python
# Initialize framework
framework = MemoryEvaluationFramework()

# Get Layer 2 test cases
layer2_tests = framework.list_test_cases(layer=2)

# Run evaluation
for test in layer2_tests:
    # Provide conversation histories to agent
    histories = framework.get_conversation_histories(test.test_id)
    agent.load_memories(histories)
    
    # Get agent's response
    question = framework.get_user_question(test.test_id)
    response = agent.respond(question)
    
    # Evaluate
    result = framework.evaluate_response(test.test_id, response)
    print(f"{test.test_id}: {'PASS' if result.reward >= 0.6 else 'FAIL'}")
    print(f"  Reward: {result.reward:.3f}/1.000")
    print(f"  Feedback: {result.feedback}")
```

## Scoring Rubric

### Layer 1 (Basic Recall)
- **100%**: All specific details recalled accurately
- **80%**: Most details correct, minor omissions
- **60%**: Key information present but some errors
- **40%**: Partial recall with significant gaps
- **20%**: Minimal accurate recall
- **0%**: No relevant information retrieved

### Layer 2 (Disambiguation)
- **100%**: All relevant items identified and presented
- **80%**: Most items identified, clear disambiguation
- **60%**: Some items missed but attempts disambiguation
- **40%**: Partial retrieval, weak disambiguation
- **20%**: Single item retrieved when multiple exist
- **0%**: No relevant retrieval or wrong information

### Layer 3 (Synthesis)
- **100%**: Complete synthesis with proactive insights
- **80%**: Good synthesis, some proactive elements
- **60%**: Basic synthesis across sessions
- **40%**: Limited cross-session connection
- **20%**: Single session focus, no synthesis
- **0%**: No synthesis or irrelevant response

## Best Practices

1. **Realistic Scenarios**: Use actual business scenarios and terminology
2. **Natural Language**: Avoid overly formal or structured language
3. **Progressive Complexity**: Start simple, add complexity naturally
4. **Domain Expertise**: Include industry-specific details and concerns
5. **Temporal Elements**: Include dates, deadlines, expiration dates
6. **Financial Details**: Use realistic prices, fees, calculations
7. **Personal Information**: Use consistent fake identities across tests
8. **Error Patterns**: Include common human errors and corrections

## Extension Points

1. **Industry Verticals**: Add specialized test cases for specific industries
2. **Language Variants**: Create multilingual test cases
3. **Temporal Reasoning**: Add tests for time-sensitive information
4. **Emotional Context**: Include sentiment and relationship dynamics
5. **Multi-modal**: Extend to include document/image references
6. **Group Dynamics**: Add multi-party conversation scenarios

## Maintenance Guidelines

1. **Regular Updates**: Update prices, dates, regulations quarterly
2. **Coverage Analysis**: Ensure even distribution across domains
3. **Difficulty Calibration**: Adjust based on agent performance data
4. **Edge Cases**: Continuously add discovered edge cases
5. **Feedback Integration**: Incorporate user feedback and failures

## Conclusion

This framework provides a systematic approach to evaluating agent memory capabilities across three critical dimensions. By progressing from basic recall through disambiguation to synthesis, it ensures comprehensive assessment of an agent's ability to function as a true personal assistant.
