import SharedRecommendations from '../recommendations/Recommendations'
import apiClient from '../api/client'
const errorText=error=>typeof error.response?.data?.detail==='string'?error.response.data.detail:'Recommendations could not load. Refresh before retrying.'
async function readRecommendations(id){try{return {ok:true,data:(await apiClient.get(`/api/businesses/${encodeURIComponent(id)}/recommendations`)).data}}catch(error){return {ok:false,error:errorText(error)}}}
async function recommendationCommand(id,command,payload,planId=''){try{const root=`/api/businesses/${encodeURIComponent(id)}/recommendations`,path=root+(command==='create'?'':`/${encodeURIComponent(planId)}${command==='decision'?'/decision':''}`);const response=command==='revise'?await apiClient.put(path,payload):await apiClient.post(path,payload);return {ok:true,data:response.data}}catch(error){return {ok:false,error:errorText(error)}}}
export default function Recommendations(props){return <SharedRecommendations key={`${props.businessId}:${props.role}:${props.boardroom}`} {...props} readRecommendations={readRecommendations} recommendationCommand={recommendationCommand}/>}
