import hmac
import hashlib
import base64
from datetime import datetime

def generate_aba_payway_hash(data, api_key):
    """
    Generate hash for ABA PayWay Purchase API
    
    Args:
        data: Dictionary containing payment data
        api_key: Your ABA PayWay API Key (Public Key)
    """
    # Concatenate fields in the exact order required by PayWay
    hash_string = (
        str(data.get('req_time', '')) +
        str(data.get('merchant_id', '')) +
        str(data.get('tran_id', '')) +
        str(data.get('amount', '')) +
        str(data.get('items', '')) +
        str(data.get('shipping', '')) +
        str(data.get('firstname', '')) +
        str(data.get('lastname', '')) +
        str(data.get('email', '')) +
        str(data.get('phone', '')) +
        str(data.get('type', '')) +
        str(data.get('payment_option', '')) +
        str(data.get('return_url', '')) +
        str(data.get('cancel_url', '')) +
        str(data.get('continue_success_url', '')) +
        str(data.get('currency', ''))
    )
    
    # Generate HMAC SHA-512 hash
    hash_obj = hmac.new(
        api_key.encode('utf-8'),
        hash_string.encode('utf-8'),
        hashlib.sha512
    )
    
    # Base64 encode the hash
    return base64.b64encode(hash_obj.digest()).decode('utf-8')
