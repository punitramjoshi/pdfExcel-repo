# excel_model.py
from langchain.globals import set_debug
from langchain_openai import ChatOpenAI
from pandasai import SmartDataframe
from typing import Union
import pandas as pd
import requests
import re
import io
import os
from dotenv import load_dotenv

load_dotenv(override=True)

set_debug(True)

class ExcelBot:
    def __init__(self, file_path: str, sheet_name: Union[str, int] = 0) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.df: pd.DataFrame = self.load_excel_file(file_path, sheet_name=sheet_name)
        self.clean_df: pd.DataFrame = self.clean_dataframe_columns(self.df)
        self.llm = ChatOpenAI(model="o3-mini", api_key=self.api_key)
        (
            self.column_value_pairs,
            self.column_list,
            self.sample_data,
        ) = self.create_metadata()
        self.smart_df = SmartDataframe(
            self.clean_df, config={"llm": self.llm, "conversational": False}
        )
        self.plot_prompt = """
You have to convert Python Matplotlib code that may use a DataFrame (`df`) to generate a chart into JavaScript (React) code that uses a JSON object (`json_data`) to generate an equivalent chart using Recharts, charting library built with React and D3.

### Detailed Instructions:

#### Input Format
1. **Matplotlib Code**: Provided code will be written in Python using the Matplotlib library for generating various types of charts (e.g., pie, bar, line).

#### Output Format
1. **Recharts Code**: Convert the provided Matplotlib code into JavaScript (React) code using the Recharts library.

### Conversion Steps

1. **Identify Chart Type**: Determine the type of chart being generated by the Matplotlib code (e.g., pie chart, bar chart, line chart).

2. **Necessary Considerations**:
- Instead of the dataframe `df` or `dfs`(list of df) that may be specified in the matplotlib code, take json object called `json_data` or a list of `json_data` in Recharts code.
- Consider that the `json_data`, created from the dataframe `df` will be loaded from a ".json" file, and that `json_data` variable is to be used in the Recharts code.
- Extract the fields, filters and other aspects of the Matplotlib code, for the creation of Recharts code.
- DO NOT make any example data in the code, just use the `json_data` or a list of `json_data` variable(s), inplace of `df` or `dfs`.

3. **Setup Recharts Components**:
- Based on the chart type, set up the corresponding Recharts components. For example:
    - `PieChart`, `Pie`, `Tooltip` for a pie chart.
    - `BarChart`, `Bar`, `XAxis`, `YAxis`, `Tooltip` for a bar chart.
    - `LineChart`, `Line`, `XAxis`, `YAxis`, `Tooltip` for a line chart.
- Ensure the data keys in the Recharts components match the structure of `json_data`.

4. **Handle Customizations**:
   - Translate any customizations in the Matplotlib code (e.g., colors, labels, titles) into the corresponding Recharts properties and components.
   - Ensure features like `autopct`, `startangle`, `figsize` in Matplotlib are appropriately handled in Recharts.

5. **Rendering**:
   - Ensure the Recharts code is structured to be part of a React component.
   - Properly render the chart within a specified width and height, similar to the `figsize` in Matplotlib.
   
REMEMBER: DO NOT include any type of instruction or explanation or any example usage to the code. Give only the Recharts code as an output."""
        self.system_prompt = """
#### Context:
You are a query refinement system designed to interpret and refine user queries based on data from an Excel file. You will receive:
1. Metadata about the data in the Excel file.
2. The first five rows of the dataframe.
3. A natural language query from the user.

#### Metadata:
- **Columns:** A list of all column names in the dataframe.
- **Columns-Values Pairs:** A dictionary where the keys are column names with less than 15 unique values, and the values are lists of those unique values, otherwise the first three values of the columns.
- **First Five Rows of Data:** The first five rows as sample of the data. Output from df.head()

#### Your Task:
1. **Understand the User Query:** Interpret the user's natural language query in the context of the provided metadata and data sample.
2. **Consider Metadata:**
- Use the list of columns to understand the scope of the data.
- Use the unique values dictionary to identify categorical columns with limited unique values that might be relevant for the query.
3. **Refine the Query:** Translate the natural language query into a refined, structured query that clearly specifies:
- Relevant columns to consider.
- Any filters or conditions based on the unique values.
- The type of information or analysis the user is seeking.
- **IMPORTANT**:- Analyze whether there is Official name or nickname of any US State in the query. If it is present, and if required as per the data, convert it into the corresponding ZIP code.

#### Output Format:
Your response should be a refined query in a structured format that can be directly used by the next component to retrieve or analyze the data. The format should be clear and unambiguous.

#### Examples:
- **User Query:** "What are the sales figures for each region?"
**Refined Query:** "Select 'Region', 'Sales' columns. Get sales figures for each unique value in 'Region'."

- **User Query:** "Show me the details of the products with sales above 1000 units."
**Refined Query:** "Filter rows where 'Sales' > 1000. Select all columns for the filtered rows."

#### Constraints:
- Ensure clarity and specificity in the refined query.
- Include any necessary conditions or filters explicitly.
- Consider all relevant columns and unique values in the metadata.
- Consider some external data like Zip Codes, State Abbreviations, Symbolic state names, etc and refine the query including this data, ONLY IF REQUIRED.
- ADHERE TO THE FORMAT OF OUTPUT SHOWN IN THE ABOVE EXAMPLES. DO NOT add any instruction or any extra text to the output.

#### Begin Processing:
Refine the user query based on the above instructions.
    """
        self.human_prompt = (
            f"""
    #### Metadata:
    Columns: {self.column_list}
    Column-Value Pairs: {self.column_value_pairs}
    Sample Data: {self.sample_data}
    """
            + """
    #### User Query:
    """
        )
        self.prompt_template = "System:\n" + self.system_prompt + self.human_prompt

    def load_excel_file(
        self, file_path_or_url: str, sheet_name: Union[str, int] = 0
    ) -> pd.DataFrame:
        def load_data(content, content_type):
            if (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                in content_type
            ):  # XLSX
                return pd.read_excel(io.BytesIO(content), sheet_name=sheet_name)
            elif "application/vnd.ms-excel" in content_type:  # XLS
                return pd.read_excel(io.BytesIO(content), sheet_name=sheet_name)
            elif "text/csv" in content_type or "application/csv" in content_type:  # CSV
                # Read initially without setting an index column
                df = pd.read_csv(io.BytesIO(content), index_col=False)
                # Check if the first column should be the index
                if (
                    df.columns[0].lower().startswith("unnamed")
                    and df.iloc[:, 0].is_unique
                ):
                    df.set_index(df.columns[0], inplace=True)
                    df.index.name = None
                return df
            else:
                raise ValueError("Unsupported file type or content type.")

        if os.path.isfile(file_path_or_url):
            # If it's a local file path, read it directly
            if file_path_or_url.endswith(".xlsx"):
                df = pd.read_excel(file_path_or_url, sheet_name=sheet_name)
            elif file_path_or_url.endswith(".xls"):
                df = pd.read_excel(file_path_or_url, sheet_name=sheet_name)
            elif file_path_or_url.endswith(".csv"):
                df = pd.read_csv(file_path_or_url, index_col=False)
                if (
                    df.columns[0].lower().startswith("unnamed")
                    and df.iloc[:, 0].is_unique
                ):
                    df.set_index(df.columns[0], inplace=True)
                    df.index.name = None
            else:
                raise ValueError("Unsupported file type for local file.")
        else:
            # Fetch the data using requests
            response = requests.get(
                file_path_or_url, headers={"User-Agent": "Mozilla/5.0"}
            )
            response.raise_for_status()  # Raise an error for bad status codes

            # Determine content type
            content_type = response.headers.get("Content-Type")

            # Read the content into a pandas DataFrame
            try:
                df = load_data(response.content, content_type)
            except ValueError as e:
                print(e)
                return pd.DataFrame()  # Return an empty DataFrame on error

        # Drop initial empty rows
        df = df.dropna(how="all").reset_index(drop=True)

        # Check if the first two rows contain strings to determine if it has a multi-level header
        if len(df) > 1:
            first_row_is_str = all(isinstance(i, str) or pd.isna(i) for i in df.iloc[0])
            second_row_is_str = all(
                isinstance(i, str) or pd.isna(i) for i in df.iloc[1]
            )
        else:
            first_row_is_str = False
            second_row_is_str = False

        if first_row_is_str and second_row_is_str:
            # If the first two rows are strings (or NaNs in the first row), it's a multi-level header
            df.columns = [
                f"{str(col[0])} {col[1]}".strip() if pd.notna(col[0]) else col[1]
                for col in df.columns.values
            ]

        # Drop initial empty rows (redundant if already done above, but keeping for completeness)
        df = df.dropna(how="all").reset_index(drop=True)

        return df

    def clean_dataframe_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        def clean_column_name(col):
            # Use regex to remove 'Unnamed: ..._level_...' patterns
            cleaned_col = re.sub(r"Unnamed: \d+_level_\d+", "", col).strip()
            return cleaned_col if cleaned_col else "Unnamed"

        # Apply the cleaning function to each column name
        cleaned_columns = [clean_column_name(col) for col in df.columns]

        # Rename the columns in the DataFrame
        df.columns = cleaned_columns

        return df

    def create_metadata(self):
        # Dictionary to hold columns with 15 or fewer unique values
        column_value_pairs = {}

        # Iterate through each column in the DataFrame
        for column in self.clean_df.columns:
            unique_values = self.clean_df[column].nunique()
            if unique_values <= 15:
                column_value_pairs[column] = self.clean_df[column].unique().tolist()

        return (
            str(column_value_pairs),
            str(list(self.clean_df.columns)),
            str(self.clean_df.head()),
        )

    def refine_query(self, query):
        prompted_query = self.prompt_template + query + "#### Refined Query:"
        self.refined_query = self.llm.invoke(prompted_query)
        return self.refined_query.content

    def is_query_valid(self, refined_query: str) -> bool:
        # Check if the refined query references columns in the DataFrame
        for column in self.clean_df.columns:
            if column.strip().lower() in refined_query.lower():
                return True
        return False

    def check_visualization_request(self, refined_query: str) -> bool:
        """
        Use the LLM to determine if the refined query contains a request for visualization.
        
        Args:
        refined_query (str): The refined query string.
        
        Returns:
        bool: True if visualization is requested, False otherwise.
        """
        visualization_check_prompt = f"""
        Analyze the following query and determine if it's requesting any form of data visualization (e.g., plot, graph, chart, diagram).
        Only respond with 'Yes' if a visualization is explicitly or implicitly requested, otherwise respond with 'No'.

        Query: {refined_query}

        Is a visualization requested (Yes/No)?
        """

        response = self.llm.invoke(visualization_check_prompt)
        return response.content.strip().lower() == 'yes'
    
    def matplotlib_to_recharts(self, plot_code):
        conversion_prompt = self.plot_prompt + f"\n\nMatplotlib Code:\n{plot_code}"
        response = self.llm.invoke(conversion_prompt).content
        if "```javascript" in response:
            response = response[14:-4]
        return response
    
    def excel_invoke(self, query: str):
        refined_query = self.refine_query(query)
        result = self.is_query_valid(refined_query)

        if not result:
            return "I don't know the answer to that question."

        is_visualization = self.check_visualization_request(refined_query)
        
        if is_visualization:
            response = self.smart_df.chat(refined_query, output_type='plot')
            with open("code.py", "r") as fp:
                plot_code = fp.read()
            self.json_data = self.clean_df.to_dict()
            recharts_code = self.matplotlib_to_recharts(plot_code)
            recharts_code
            return recharts_code, self.json_data, True
        else:
            response = self.smart_df.chat(refined_query)

        if isinstance(response, pd.DataFrame):
            response = response.to_json()
        return response, None, False