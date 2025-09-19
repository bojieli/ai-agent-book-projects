# Mock Data Generation

## Current Mock Data for the Benchmark
Feel free to use some of the data for other purposes.
- `users.json`: a database of users with their emails, addresses, and orders
- `products.json`: a database of products, where each product has variants (e.g., size, color).
- `orders.json`: a database of orders that can be operated upon.


Check `../tools` for mock APIs on top of current mock data.


### Experience of Mock Data Generation

Read our paper to learn more about the generation process for each database. In general, it involves the following stages:

1. Design the type and schema of each database. Can use GPT for co-brainstorming but has to be human decided as it is the foundation of everything else.
2. For each schema, figure out which parts can be programmaticly generated and which parts need GPT. For example,
    - Product types (shirt, lamp, pen) and user names (Sara, John, Noah) need GPT generation
    - Product price and shipping date can be generated via code
3. Use GPT to generate seed data (first names, last names, addresses, cities, etc.), then use a program to compose them with other code generated data. Can use GPT to help write the code for this part, but I think code-based database construction is more reliable than GPT-based database construction (e.g., give some example user profiles and ask GPT to generate more --- issues with diversity and reliability).
