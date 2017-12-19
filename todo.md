## Must Have Features:
- [x] Create Reservation: Input(image_id), Output(Status, Ip_addr, port, container_name)
- [x] Load Balancing Algorithm. Input(image_id), Output(Best Suited Compute Node)
- [x] Run Container. Input(image_name, Compute Node ID), Output(Status, Docker port)
- [x] Create IPTable Rules. Input(Compute Node IP addr, Docker port no)  Output(Status, NAT Port, Management IP)
- [x] Server Health Monitoring. Input(Compute Node ID) output(Available, Down)
- [ ] Container Health Monitoring.  Input(Container ID) Output (Available, Down)
- [x] Delete Reservation: Input(Container ID) Output (Status)

## Good to Have Features:
- [x] Docker registry hosted on server side.
- [ ] DHCP Server on Client side.

- Admin dashboard reload
- dashboard reload
- Column rename weight -> Capacity
- Admin dashboard compute node table, add column "current load"
-

### Minor TODOs
1. Push the registry container in registry itself.
2.