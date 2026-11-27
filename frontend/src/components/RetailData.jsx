import Retail from '../workflow/RetailData';
import api from '../api/client';
const base=id=>`/api/businesses/${encodeURIComponent(id)}/retail`;
const errorMessage=error=>typeof error.response?.data?.detail==='string'?error.response.data.detail:'Retail import unavailable. Check the preview and retry.';
async function read(id){try{return {ok:true,data:(await api.get(base(id))).data}}catch(error){return {ok:false,error:errorMessage(error)}}}
async function upload(id,action,form){try{return {ok:true,data:(await api.post(base(id)+'/'+action,form)).data}}catch(error){return {ok:false,error:errorMessage(error)}}}
export default function RetailData(props){return <Retail {...props} read={read} upload={upload}/>}
