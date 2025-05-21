import weaviate
from weaviate.classes.init import Auth
import os
import json
import atexit
from weaviate.classes.query import Rerank
from dotenv import load_dotenv
from openai import OpenAI
import instructor
from ..models.grievance_models import FollowUpQuestions

# Load environment variables
load_dotenv()

# Get configuration from environment variables
weaviate_url = os.getenv("WEAVIATE_URL")
weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
voyageai_api_key = os.getenv("VOYAGEAI_API_KEY")
collection_name = os.getenv("COLLECTION_NAME")

# Global client variable
client = None
collection = None

# Function to disconnect the client
def disconnect_client():
    """
    Properly disconnect the Weaviate client to prevent resource warnings and memory leaks.
    This function should be called when the client is no longer needed.
    """
    global client
    
    try:
        if client is not None:
            print("Closing Weaviate client connection...")
            client.close()
            print("Weaviate client connection closed successfully")
            client = None
    except Exception as e:
        print(f"Error disconnecting Weaviate client: {e}")

# Initialize Weaviate client with cloud connection
def initialize_client():
    global client, collection
    
    # If client is already initialized, return it
    if client is not None and collection is not None:
        return client, collection
        
    try:
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=Auth.api_key(weaviate_api_key),
            headers={
                'X-OpenAI-Api-Key': openai_api_key,
                'X-VoyageAI-Api-Key': voyageai_api_key
            },
            skip_init_checks=True
        )
        
        # Check if client is ready
        is_ready = client.is_ready()
        print(f"Weaviate client ready: {is_ready}")
        
        # Get the collection reference
        collection = client.collections.get(collection_name)
        
        # Register disconnect function to run at exit
        atexit.register(disconnect_client)
        
        return client, collection
        
    except Exception as e:
        print(f"Error initializing Weaviate client: {e}")
        raise

# Initialize the client and collection
try:
    client, collection = initialize_client()
except Exception as e:
    print(f"Initial client connection failed: {e}")


def fetch_category(grievance):
    """
    Fetch the correct category of grievance using vector search.
    
    Args:
        grievance (str): The grievance description to categorize
        
    Returns:
        list: List of structured category data with scores and properties
    """
    try:
        # Ensure client is initialized
        global client, collection
        if client is None or collection is None:
            client, collection = initialize_client()
            
        response = collection.query.hybrid(
            query=grievance,
            alpha=1.0,
            limit=10,
            rerank=Rerank(
                prop="description_of_Grievance_Category",
                query=grievance
            )
        )
        
        categories = response.objects
        bucket_data = []

        for i, data in enumerate(categories, 1):
            score = None
            rerank_score = None
            
            if hasattr(data.metadata, 'score') and data.metadata.score is not None:
                score = data.metadata.score
            
            if hasattr(data.metadata, 'rerank_score') and data.metadata.rerank_score is not None:
                rerank_score = data.metadata.rerank_score
            
            result = {
                "rank": i,
                "score": score,  # Use the extracted score
                "rerank_score": rerank_score,  # Add the rerank_score
                "id": data.properties.get("uuid"),
                "concat_grievance_category": data.properties.get("concat_Grievance_Category"),
                "content": data.properties.get("description_of_Grievance_Category"),
                "department_code": data.properties.get("department_Code"),
                "department_name": data.properties.get("department_Name"),
                "category": data.properties.get("category"),
                "sub_category_1": data.properties.get("sub_Category_1"),
                "sub_category_2": data.properties.get("sub_Category_2"),
                "sub_category_3": data.properties.get("sub_Category_3"),
                "sub_category_4": data.properties.get("sub_Category_4"),
                "sub_category_5": data.properties.get("sub_Category_5"),
                "sub_category_6": data.properties.get("sub_Category_6"),
                "description_of_grievance_category": data.properties.get("description_of_Grievance_Category"),
                "gpt_form_field_generation": data.properties.get("gPT_Form_Field_Generation"),
            }
            bucket_data.append(result)
            print(result)
            
        return bucket_data
    except Exception as e:
        print(f"Error fetching categories: {e}")
        return []


def process_grievance_category(grievance_text):
    """
    Process a grievance description to extract category information and form fields.
    
    Args:
        grievance_text (str): The grievance description to categorize
        
    Returns:
        dict: A dictionary containing category information and formatted fields
            {
                'categories': list of category objects,
                'top_category': the top matching category,
                'formatted_fields': formatted string of form fields,
                'classified_category': string representation of the category path
            }
    """
    try:
        # Fetch potential categories
        categories = fetch_category(grievance_text)
        
        if not categories or len(categories) == 0:
            print("No matching categories found")
            return {
                'categories': [],
                'top_category': None,
                'formatted_fields': "",
                'classified_category': ""
            }
        
        top_category = categories[0]
        
        # Extract form fields from the top category
        try:
            form_fields_str = top_category.get('gpt_form_field_generation', '[]')
            # Handle the case where the string might not be a complete JSON array
            if form_fields_str and not form_fields_str.startswith('['):
                form_fields_str = '[' + form_fields_str + ']'
            form_fields = json.loads(form_fields_str)
        except json.JSONDecodeError as e:
            print(f"Error parsing form fields JSON: {e}")
            form_fields = []
        
        # Create a formatted string representation of the form fields
        formatted_fields = ""
        for field in form_fields:
            formatted_fields += f"Field: {field.get('field_name', 'Unknown')}\n"
            formatted_fields += f"Data Type: {field.get('data_type', 'Unknown')}\n"
            formatted_fields += f"Mandatory: {field.get('mandatory', False)}\n"
            formatted_fields += f"Description: {field.get('description', '')}\n"
            if 'options' in field:
                formatted_fields += f"Options: {', '.join(field.get('options', []))}\n"
            formatted_fields += "---\n\n"
        
        # Get the classified category path
        classified_category = top_category.get('concat_grievance_category', '')
        
        return {
            'categories': categories,
            'top_category': top_category,
            'formatted_fields': formatted_fields,
            'classified_category': classified_category
        }
    except Exception as e:
        print(f"Error processing grievance category: {e}")
        return {
            'categories': [],
            'top_category': None,
            'formatted_fields': "",
            'classified_category': ""
        }


def generate_follow_up_questions(grievance, category, required_fields):
    ins_client = instructor.from_openai(OpenAI())

    prompt = f"""
    You are an AI assistant helping with grievance categorization analysis. 
    
    USER GRIEVANCE:
    {grievance}
    
    ASSIGNED CATEGORY:
    {category}
    
    REQUIRED FORM FIELDS:
    {required_fields}
    
    Please analyze:
    1. Is this grievance correctly categorized? Why or why not?
    2. Based on the user grievance, what information is missing that would be required by the form fields?
    3. What follow-up questions should be asked to gather the missing information?
    """ 

    try:
        response = ins_client.chat.completions.create(
            model="gpt-4.1-mini",
            response_model=FollowUpQuestions,
            messages=[
                {"role": "system", "content": "You are an AI assistant that analyzes grievance categorizations and identifies missing information."},
                {"role": "user", "content": prompt}
            ],
        )
        
        return response
    except Exception as e:
        print(f"Error generating follow-up questions: {e}")
        return None
        