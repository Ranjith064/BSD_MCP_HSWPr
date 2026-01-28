void PRC_RBBLA_STP0OutputX2 (void)
{
    boolean  l_BlaOutput_B;        /*local variable BLA outputactuation*/
    uint16 l_MESG_BlaAct_u16; /* Bla Actuation Message for control of BLA output pin */
    ToyVehicleCfg_ST l_VehicleCfg_ST; /* vehicle with BLA relay */
    
    RcvMESG( l_VehicleCfg_ST, MESG_VehicleCfg_ST);
    
    RBMESG_SendMESG( RBMESG_BlaAvailableHSW_B, TRUE );
    RBMESG_RcvMESG( l_MESG_BlaAct_u16, RBMESG_BlaAct_u16 );
    
    if( l_MESG_BlaAct_u16 != 0)
    {
        l_BlaOutput_B = TRUE;
    }
    else
    {
        l_BlaOutput_B = FALSE;
    }
}