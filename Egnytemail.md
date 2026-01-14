Hi Jan,

Great speaking with you today! 

I have created a sandbox and added you as an admin, you should have received the email invitation (2 emails were already sent for admin and user access, please accept the admin access first).

Please find important information below to help you build and publish your integration - 

Additional users (for dev. and testing) can be added by going to Settings (left side bar) > Users & Groups > Add New Account.

An admin on the sandbox domain will need to create a developer account here https://developers.egnyte.com/member/register, once you create your account and validate your email, you should sign in to your account, and choose "apps" from the drop down menu on the top right, next to your user name. From there you will be able to create a new app, by providing the name and additional information - 
Please use the Egnyte sandbox domain we provided to you. 
Make sure the "Type" is set to "Publicly Available Application". 
Choose the API products that you would want to use "Connect" (Egnyte File Server) "Secure & Govern" Egnyte compliance and governance product or both.
You will then be issued an API key and, following a verification by our team, the key will be activated. 

Important notes: 
At this point, your app and API key will be tied to your sandbox environment and will not be accessible from any production or other sandbox environment. In order to make your integration publicly available, it will need to go through a certification process (see below). 
Default API key limits are set to 2 QPS /1.000 daily. Note: rates apply per Egnyte user, and usage by 1 user will not consume the rates for other users/customers. If needed, these limits can be somewhat increased, but will not be unlimited. Increased rate is usually provided for keys already in production (past certification) but in certain cases can be provided pre certification for testing purposes. To request for increased rates, please send us an email with the API key for which you are requesting the increased rates for, the use case - mainly what APIs are you using, which type of calls (e.g. upload, download, produce reports, metadata reading/writing) - and the reasoning for the increased rates (a customer is hitting the quota,  the use case is expected to need higher rates etc.). 
Please find here links to the Egnyte API documentation and the Egnyte Integrations Cookbook - A guided "recipe" like approach to our API
It is advised to understand how permissions work at Egnyte. At a high level, each and every folder and sub-folder could have a different set of permissions, and will not necessarily inherit permissions from the parent folder. You can learn more about it here.  
Certification process - 
The objectives of the certification process are (1) to make sure your application is maintaining security when accessing Egnyte APIs; and (2) provide a more seamless experience for our customers when enabling the integration. In order to be certified, an app must implement OAuth flow.
When you complete development and ready to be certified, please submit these 2 forms -
Technical Certification Form - On the technical side, we want to make sure the application is working smoothly, and that all authentication and security protocols are maintained. Once this form is submitted, our team will review it and will either certify your app or have questions for your team. The certification can take up to 3 weeks, although our goal is to make it much quicker than that, it depends on the team's bandwidth at the time of submission. 
App Content Form - A marketing form for the content you would like to show in your listing on the Egnyte's Apps & Integrations page. Note: this page is available through our website, but is also available within our product, and the majority of the views come from Egnyte existing customers/users and our own team members, so the content of the listing should explain the benefits of the integration, for those users, as well as the solution.

If you have any questions or issues, technical or others, please reach back out to us.

Best,
Bryn