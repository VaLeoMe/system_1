
# CheeseChainPrivate

Design and Implementation of a Database-to-Blockchain Data Gathering Solution for Cheese Tracking

## Installation

*Note: The commands might be slightly different depending on the operating system*

1. Clone the project.
2. Create a Docker Hub account, if necessary, and login: \
**sudo docker login**
3. Deploy the SC[^1] and fetch a new refresh token[^2]. Then, add these two pieces of information, along with your wallet and the RPC endpoint addresses, to the **Config.json** file.
5. Initialize a Docker swarm: \
**sudo docker swarm init**
6. Register the Docker secrets in the swarm:\
**echo "RPC-NODE-ADDRESS" | sudo docker secret create http\_provider -**\
**echo "PRIVATE-KEY" | sudo docker secret create private\_key -**\
**echo "WALLET-PASSWORD" | sudo docker secret create metamask\_password -**
7. Build the image: \
**sudo docker build -t \<DOCKER-HUB-USERNAME\>/system\_1:tag .**
8. Publish the image on Docker Hub: \
**sudo docker push \<DOCKER-HUB-USERNAME\>/system\_1:tag**
10. Deploy the stack: \
**sudo docker stack deploy -c docker-compose.yml mystack**

[^1]: If Remix is used for the deployment, using the compiler **0.8.8+commit.dddeac2f** is recommended.
[^2]: Log in to [https://qs.fromarte.ch](https://qs.fromarte.ch) with the developer tools open and copy the refresh-token from the network tab.

## Synchronization
The files are synchronized onto the host and the BC, with the ID (e.g. RG9jdW1lbnQ6MDg2Yzc3ODAtNDZlYS00Y2IyLThlMWQtMjliZmU0MzQ2NWYy) forms can be fetched form the BC trough the remix IDE. 
In the folder `BackupFiles` the corresponding files with the relevant information can be found, aswell as all **RUNNING** forms in the `BackUp.json` file in the main directory.

## Authors

- [@Dave5252](https://github.com/Dave5252)
- [@VaLeoMe](https://github.com/VaLeoMe)


    
