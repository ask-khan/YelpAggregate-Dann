import requests, json

token_url = "https://api.outreach.io/oauth/token"
callback_uri = "https://www.virtbrands.com/oauth/outreach"
account_api_url = "https://api.outreach.io/api/v2/accounts"
prospect_api_url = "https://api.outreach.io/api/v2/prospects"

client_id = 'YtM5gPQka9igO9rvIkJKE8FINpwlqGQnCC-PfM3KabA'
client_secret = 'zGwDrdaokSZEaHJTO_WXSXZGWBLAo9hI46_QlNoCsTE'
refresh_token = 'NZ0l4KRQnyZ5Jfz2e0KDWIVCqpdxVb9hzQazxVC1TZw'

# scope = 'prospects.all accounts.all'

# authorization_redirect_url = authorize_url + '?response_type=code&client_id=' + client_id + '&redirect_uri=' + callback_uri + '&scope=' + scope
# print ("go to the following url on the browser and enter the code from the returned url: ")
# print ("---  " + authorization_redirect_url + "  ---")
# authorization_code = input('code: ')

def getAccountByCustomId(s, customId):
    response = s.get(account_api_url + '?filter[customId]=' + customId)
    try:
        account = json.loads(response.text)
        if(account):
            try:
                return account['data'][0]
            except IndexError:
                return False
            except KeyError:
                return False
    except ValueError:
        return False

def getProspectByAccountId(s, accountId, emails):
    response = s.get(prospect_api_url + '?filter[account][id]=' + str(accountId))
    try:
        prospect = json.loads(response.text)
        if(prospect):
            try:
                return prospect['data'][0]
            except IndexError:
                return False
            except KeyError:
                return False
    except ValueError:
        return False

def formatParam(updatedData, oldData):
    newData = {}
    try:
        for attr, value in updatedData.items():
            if not attr == 'id' and (not oldData[attr] or oldData[attr] == 'null'):
                newData[attr] = value
    except:
        return {}
    return newData

def updateOutreach(s, account, prospect, existingAccount):
    updatedAccountAttributes = formatParam(account, existingAccount['attributes'])
    if updatedAccountAttributes:
        accountPayload = json.dumps({
        "data": {
            "type": "account",
            "id": existingAccount['id'],
            "attributes": updatedAccountAttributes
            }
        })
        
        accountResponse = s.patch(account_api_url + '/' + str(existingAccount['id']), data=accountPayload)
        try:
            account = json.loads(accountResponse.text)

            print('update the account', accountResponse.text)
            if(account):
                try:
                    existingProspect = getProspectByAccountId(s, existingAccount['id'], prospect['emails'])
                    if existingProspect:
                        updatedProspectAttributes = formatParam(prospect, existingProspect['attributes'])
                        if(updatedProspectAttributes):
                            prospectPayload = json.dumps({
                                "data": {
                                    "type": "prospect",
                                    "id": existingProspect['id'],
                                    "attributes": updatedProspectAttributes,
                                    "relationships": {
                                        "account": {
                                            "data": {
                                                "type": "account",
                                                "id": existingAccount['id']
                                            }
                                        }
                                    }
                                }
                            })
                            prospectResponse = s.patch(prospect_api_url + '/' + str(existingProspect['id']), data=prospectPayload)
                            print('update the prospect', prospectResponse.text)
                    else:
                        print('The prospect does not exist')
                        try:
                            prospectPayload = json.dumps({
                                "data": {
                                    "type": "prospect",
                                    "attributes": prospect,
                                    "relationships": {
                                        "account": {
                                            "data": {
                                                "type": "account",
                                                "id": existingAccount['id']
                                            }
                                        }
                                    }
                                }
                            })
                            prospectResponse = s.post(prospect_api_url, data=prospectPayload)
                            print('create a new prospect', prospectResponse.text)
                        except KeyError:
                            pass
                except KeyError:
                    pass
        except ValueError:
            pass

def createOutreach(s, account, prospect):
    accountPayload = json.dumps({
        "data": {
            "type": "account",
            "attributes": account
        }
    })
    
    accountResponse = s.post(account_api_url, data=accountPayload)
    try:
        account = json.loads(accountResponse.text)

        print('create a new account', accountResponse.text)
        if(account):
            try:
                prospectPayload = json.dumps({
                    "data": {
                        "type": "prospect",
                        "attributes": prospect,
                        "relationships": {
                            "account": {
                                "data": {
                                    "type": "account",
                                    "id": account['data']['id']
                                }
                            }
                        }
                    }
                })
                prospectResponse = s.post(prospect_api_url, data=prospectPayload)
                print('create a new prospect', prospectResponse.text)
            except KeyError:
                pass
    except ValueError:
        pass

def importToOutreach(accounts=[], prospects=[]):  
    try:
        s = requests.session()
        data = {'grant_type': 'refresh_token', 'refresh_token': refresh_token, 'redirect_uri': callback_uri, 'client_id': client_id, 'client_secret': client_secret}
        access_token_response = s.post(token_url, data=data)
        # print("token response:" + access_token_response.text)
        tokens = json.loads(access_token_response.text)
        access_token = tokens['access_token']
        # print ("access token: " + access_token)

        api_call_headers = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
        s.headers = api_call_headers

        for i in range(len(accounts)):
            existingAccount = getAccountByCustomId(s, accounts[i]['customId'])
            if existingAccount:
                # update
                updateOutreach(s, accounts[i], prospects[i], existingAccount)
            else:
                # create
                createOutreach(s, accounts[i], prospects[i])
    except ValueError:
        return ("Please click the import button again!")

    print("done")
    return("Finished!")