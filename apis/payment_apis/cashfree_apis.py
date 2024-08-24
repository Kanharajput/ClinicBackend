from fastapi import APIRouter, Depends, HTTPException
from cashfree_pg.models.create_order_request import CreateOrderRequest
from cashfree_pg.api_client import Cashfree
from cashfree_pg.models.customer_details import CustomerDetails
from cashfree_pg.models.order_meta import OrderMeta
import os
from dotenv import load_dotenv
from models.users import User
from models.orders import Order
from sqlalchemy import select, update, insert
from database_conf.db_setup import get_session


payment_api = APIRouter()

# load the env variable
load_dotenv()

# initialise the variables
CASHFREE_SECRET_ID = os.getenv('CASHFREE_SECRET_ID')
CASHFREE_SECRET_KEY = os.getenv('CASHFREE_SECRET_KEY')

# initialise the CashFree attributes
Cashfree.XClientId = CASHFREE_SECRET_ID
Cashfree.XClientSecret = CASHFREE_SECRET_KEY
Cashfree.XEnvironment = Cashfree.XSandbox
x_api_version = "2023-08-01"


@payment_api.post("/generate-oder/{user_id}")
async def generate_order(user_id:int, session = Depends(get_session)):
	# fetch user details
	user_data_query = select(User.phone_number).filter_by(id=user_id)
	user_data = session.execute(user_data_query).fetchone()

	# user_data tuple contains phone_number at index 0 and id at index 1
	phone_number_without_code  = str(user_data[0].split(" ")[1])

	# cashfree wants three digits unique customer id
	if len(str(user_id)) == 1:
		user_id = "00" + str(user_id)
	
	elif len(str(user_id)) == 2:
		user_id = "0" + str(user_id)

	# pass user details to cashfree
	customerDetails = CustomerDetails(customer_id=str(user_id), customer_phone=phone_number_without_code)
	createOrderRequest = CreateOrderRequest(order_amount=1, order_currency="INR", customer_details=customerDetails)

	# creating a meta data
	orderMeta = OrderMeta()        
	orderMeta.return_url = "https://www.cashfree.com/devstudio/preview/pg/web/popupCheckout?order_id={order_id}"
	createOrderRequest.order_meta = orderMeta

	try:
		api_response = Cashfree().PGCreateOrder(x_api_version, createOrderRequest, None, None)
		# check order created successfully or not
		if api_response.data.order_status == "ACTIVE":
			# store order_id and order_status
			insert_order_details_query = insert(Order).values(user_id=user_id, order_id = api_response.data.order_id, order_status=api_response.data.order_status )
			session.execute(insert_order_details_query)
			session.commit()
			return {"payment_session_id": api_response.data.payment_session_id}
		
	except Exception as e:
		print(e)
		raise HTTPException(500, "Something went wrong")


@payment_api.get("/fetch-order-id/{user_id}")
async def fetch_order_id(user_id:int, session = Depends(get_session)):
	# fetch order_id
	fetch_order_id_query = select(Order.order_id).filter_by(id=user_id)
	order_id = session.execute(fetch_order_id_query).scalar()
	# order found 
	if order_id:
		api_response = Cashfree().PGOrderFetchPayments(x_api_version, order_id, None)
		payments = api_response.data
		# if no payment is made then payments is an empty list
		if payments:
			for attempted_payment in payments:
				if attempted_payment.payment_status == "SUCCESS":
					# save this details to database for further enquiry
					return {"payment_status":"Success", "payment_time": attempted_payment.payment_time, "payment_method": attempted_payment.payment_method}
				
				if attempted_payment.payment_status == "FAILED":
					# save this details to database for further enquiry
					return {"payment_status":"FAILED", "payment_time": attempted_payment.payment_time, "payment_method": attempted_payment.payment_method}
				
		else:
			raise HTTPException(400, "No Payment made till now")

	else:
		raise HTTPException(400, "Order not found")
		
